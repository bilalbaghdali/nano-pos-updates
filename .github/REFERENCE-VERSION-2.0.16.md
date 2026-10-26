# NANO POS reference version

- Reference release: **v2.0.16**
- Reference release URL: https://github.com/bilalbaghdali/nano-pos-updates/releases/tag/v2.0.16
- Official input patch: `NANO-POS-Patch-1.0.118-to-2.0.16-GENERAL-IMPROVEMENTS-NO-PRAYER.zip`
- Input patch SHA-256: `c1de6142d92b6d41bc4767c8c1feb1d946687e39b0d6c74a264bc81367b49630`
- Input app.asar SHA-256: `09ca5848787cff21b6bd99c5a0d718d39586085290b97f8b5eb366317277b439`
- Reference Windows installer asset: `NANO-POS-Setup-2.0.16-x64.exe`
- Future baseline builds should start from the verified v2.0.16 release asset unless the project owner selects a different reference.
- v2.0.16 does not contain the prayer-times feature and retains localized cart-price speech.

The installer workflow validates both input SHA-256 values before packaging Electron x64 and publishing the EXE/checksum to the existing v2.0.16 release. Customer data, activation and backups are not stored in the installer output directory.
