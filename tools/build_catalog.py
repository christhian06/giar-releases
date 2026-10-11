#!/usr/bin/env python3
"""Gera docs/catalog.json a partir dos GitHub Releases deste repositório.

Convenção de tags (uma release por produto e versão):
    android-v1.2.3
    windows-v1.2.3
    firmware-<ambiente>-v4.2.1      ex.: firmware-esp32c3_v4_temp_usb-v4.2.1

Release marcada como "pre-release" vai para o canal "beta"; as demais, "stable".
Em cada canal vale a MAIOR versão de cada produto. O catálogo é o que o app
GIAR e a página de downloads consultam.

Uso:
    GH_TOKEN=... python tools/build_catalog.py --repo christhian06/giar-releases
    python tools/build_catalog.py --releases-file tests/releases.json   # teste local
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import urllib.request
import zipfile
import io
from datetime import datetime, timezone

TAG = re.compile(r"^(?P<product>android|windows|firmware)(?:-(?P<env>[A-Za-z0-9_]+))?-v(?P<ver>\d+\.\d+\.\d+)$")
ASSET_PATTERN = {
    "android": re.compile(r"\.apk$"),
    "windows": re.compile(r"^GIAR-Setup-.*\.exe$"),
    "firmware": re.compile(r"\.giarfw$"),
}


def semver(v):
    return tuple(int(x) for x in v.split("."))


def load_releases(args):
    if args.releases_file:
        with open(args.releases_file, encoding="utf-8") as f:
            return json.load(f)
    out = subprocess.run(
        ["gh", "api", f"repos/{args.repo}/releases", "--paginate", "--slurp"],
        check=True, capture_output=True, text=True).stdout
    pages = json.loads(out)
    return [r for page in pages for r in page]


def fetch(url):
    with urllib.request.urlopen(url, timeout=120) as r:
        return r.read()


def describe_asset(product, asset):
    """Baixa o arquivo para calcular SHA-256 (e ler o manifesto, no firmware)."""
    data = fetch(asset["browser_download_url"])
    info = {
        "url": asset["browser_download_url"],
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    declared = asset.get("size")
    if declared is not None and declared != len(data):
        raise SystemExit(f"Tamanho divergente em {asset['name']}: {declared} != {len(data)}")
    if product == "firmware":
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            m = json.loads(z.read("manifest.json"))
        info.update({
            "model": m.get("model"),
            "variant": m.get("variant"),
            "chip": m.get("chip"),
            "platformio_env": m.get("platformio_env"),
            "signing_key_id": m.get("signing_key_id"),
            "signed": "manifest.sig" in z.namelist(),
        })
    return info


def build(releases):
    channels = {"stable": {}, "beta": {}}
    for rel in releases:
        if rel.get("draft"):
            continue
        m = TAG.match(rel.get("tag_name", ""))
        if not m:
            continue
        product, env, ver = m["product"], m["env"], m["ver"]
        if (product == "firmware") != (env is not None):
            continue  # firmware exige ambiente; android/windows não
        pattern = ASSET_PATTERN[product]
        assets = [a for a in rel.get("assets", []) if pattern.search(a["name"])]
        if len(assets) != 1:
            print(f"AVISO: {rel['tag_name']} ignorada ({len(assets)} arquivos candidatos)", file=sys.stderr)
            continue
        channel = channels["beta" if rel.get("prerelease") else "stable"]
        bucket = channel.setdefault("firmware", {}) if product == "firmware" else channel
        key = env if product == "firmware" else product
        current = bucket.get(key)
        if current and semver(current["version"]) >= semver(ver):
            continue
        entry = {
            "version": ver,
            "released": rel.get("published_at"),
            "notes": (rel.get("body") or "").strip()[:600],
            "release_url": rel.get("html_url"),
        }
        entry.update(describe_asset(product, assets[0]))
        bucket[key] = entry
    return {
        "schema": 1,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "channels": channels,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="christhian06/giar-releases")
    ap.add_argument("--releases-file")
    ap.add_argument("--out", default="docs/catalog.json")
    args = ap.parse_args()
    catalog = build(load_releases(args))
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"{args.out}: " + ", ".join(
        f"{ch}={len(v) - (1 if 'firmware' in v else 0) + len(v.get('firmware', {}))}"
        for ch, v in catalog["channels"].items()))


if __name__ == "__main__":
    main()
