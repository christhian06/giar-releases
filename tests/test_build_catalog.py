import hashlib
import io
import json
import os
import sys
import tempfile
import zipfile
import pathlib
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import build_catalog  # noqa: E402


def giarfw(version, env="esp32c3_v4_temp_usb", variant="usb"):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("manifest.json", json.dumps({
            "version": version, "model": "GIAR Sensor", "variant": variant,
            "chip": "esp32c3", "platformio_env": env, "signing_key_id": "k"}))
        z.writestr("manifest.sig", "x")
        z.writestr("firmware.bin", b"1234")
    return buf.getvalue()


class CatalogTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def asset(self, name, data):
        p = self.dir / name
        p.write_bytes(data)
        return {"name": name, "size": len(data), "browser_download_url": p.as_uri()}

    def release(self, tag, assets, prerelease=False, draft=False):
        return {"tag_name": tag, "assets": assets, "prerelease": prerelease, "draft": draft,
                "published_at": "2026-10-11T00:00:00Z", "html_url": "https://x/" + tag, "body": "notas"}

    def test_picks_highest_stable_and_separates_beta(self):
        rels = [
            self.release("android-v1.0.0", [self.asset("a100.apk", b"apk100")]),
            self.release("android-v1.1.0", [self.asset("a110.apk", b"apk110")]),
            self.release("android-v1.2.0", [self.asset("a120.apk", b"apk120")], prerelease=True),
            self.release("windows-v1.0.0", [self.asset("GIAR-Setup-1.0.0.exe", b"exe")]),
            self.release("firmware-esp32c3_v4_temp_usb-v4.2.1", [self.asset("f421.giarfw", giarfw("4.2.1"))]),
            self.release("firmware-esp32c3_v4_temp_usb-v4.10.0", [self.asset("f4100.giarfw", giarfw("4.10.0"))]),
            self.release("firmware-esp32c3_v4_temp-v4.2.1", [self.asset("fb.giarfw", giarfw("4.2.1", "esp32c3_v4_temp", "battery"))]),
        ]
        c = build_catalog.build(rels)
        st = c["channels"]["stable"]
        self.assertEqual(st["android"]["version"], "1.1.0")
        self.assertEqual(st["android"]["sha256"], hashlib.sha256(b"apk110").hexdigest())
        self.assertEqual(c["channels"]["beta"]["android"]["version"], "1.2.0")
        self.assertEqual(st["windows"]["version"], "1.0.0")
        fw = st["firmware"]
        self.assertEqual(fw["esp32c3_v4_temp_usb"]["version"], "4.10.0")  # semver, não texto
        self.assertEqual(fw["esp32c3_v4_temp"]["variant"], "battery")
        self.assertTrue(fw["esp32c3_v4_temp_usb"]["signed"])

    def test_ignores_drafts_bad_tags_and_ambiguous_assets(self):
        rels = [
            self.release("android-v2.0.0", [self.asset("d.apk", b"x")], draft=True),
            self.release("random-tag", [self.asset("r.apk", b"x")]),
            self.release("android-v3.0.0", [self.asset("1.apk", b"x"), self.asset("2.apk", b"y")]),
            self.release("firmware-v4.2.1", [self.asset("n.giarfw", giarfw("4.2.1"))]),
        ]
        c = build_catalog.build(rels)
        self.assertEqual(c["channels"]["stable"], {})


if __name__ == "__main__":
    unittest.main()
