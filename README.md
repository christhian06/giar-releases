# GIAR — Releases

Repositório **público** só com os artefatos distribuídos (sem código-fonte):
aplicativo Android (APK), aplicativo Windows (instalador) e pacotes de firmware dos sensores.

- Página de downloads: https://christhian06.github.io/giar-releases/
- Catálogo (lido pelos aplicativos): https://christhian06.github.io/giar-releases/catalog.json

## Como as versões chegam aqui

Os repositórios de código (privados) publicam uma release aqui ao receber uma tag:

| Repositório | Tag de origem | Release criada aqui |
|---|---|---|
| giar-config | `v1.2.3` | `android-v1.2.3` (APK) e `windows-v1.2.3` (instalador) |
| giar-firmware | `fw-v4.2.1` | `firmware-<ambiente>-v4.2.1` (um `.giarfw` assinado por ambiente) |

Marcar a release como **pre-release** a coloca no canal `beta`; as demais vão para `stable`.
O workflow *Atualizar catálogo* regenera `docs/catalog.json` a cada release.
Não crie releases à mão com tags fora desse padrão: elas são ignoradas.

## Segredos (nos repositórios de código)

`RELEASES_TOKEN` (PAT com *Contents: write* neste repositório), `CONFIG_REPO_TOKEN` (leitura do giar-config, usado pelo firmware),
`GIAR_FW_SIGNING_KEY` (chave privada Ed25519 de assinatura do firmware, base64), e as do keystore Android
(`ANDROID_KEYSTORE_B64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD`).

## Verificar um download

O catálogo traz o SHA-256 de cada arquivo. Pacotes de firmware também levam assinatura Ed25519
verificada pelo aplicativo antes de gravar.
