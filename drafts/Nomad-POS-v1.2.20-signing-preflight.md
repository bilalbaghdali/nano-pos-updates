# Nomad POS — Android release signing preflight (19 October 2026)

**Status: NOT published to end users.** The v1.2.20 source is prepared, but a compatible signed APK has NOT been built or verified. Do **not** publish `nomad-android/latest.json` with an unverified download URL.

## Verified signing certificate SHA-256 fingerprints

| Existing APK | Certificate SHA-256 |
|---|---|
| v1.2.17 | `60FFFBF4EB205EDB4F14F1DF7E9CC5A92CF90C7A8422B2020B2FB16FED4B2B87` |
| v1.2.18 | `299469E0F3010B267363D755F4205BE2EE9CB9F4FD2AE3ACA2688BFBBD451AFE` |
| v1.2.19 | `63613971B2ED91CE044CEA6403ACC73F62D9B666ABDDDC2149436C37A4A17C99` |

All three certificate fingerprints differ, so an ordinary in-place Android update cannot be assumed safe across these builds. No `.jks`, `.keystore`, `.p12`, or `.pfx` file was found inside the available 1.2.19/1.2.20 source archives. GitHub Actions secret values cannot be retrieved. The signing key may still exist on the owner's Windows development machine.

## Required checks before publishing

1. Locate the **private signing key** for the exact APK installed on the phone. Use `keytool -list -v -keystore YOUR_KEY.jks` locally, and compare the public SHA256 certificate fingerprint. Never upload the private key, key password, or encoded keystore to a public GitHub repository.
2. Confirm the installed APK package name and the source applicationId match (`com.nanopos.nomad.fresh5` in current v1.2.20 source).
3. Configure GitHub Actions signing secrets and pin `NOMAD_CERT_SHA256`; never generate a different keystore in CI for each build.
4. Build a signed v1.2.20 APK; verify certificate, versionCode, manifest and SHA-256. Test upgrading an existing activated installation without data loss.
5. Publish the APK to a tagged GitHub Release. **Only after success** publish `nomad-android/latest.json`, containing actual download URL, SHA-256, version code/name and release notes.

The in-app update notification can appear after login **only in an app build that already includes the update checker**. Older APKs cannot gain the code merely by changing GitHub metadata.

If the original signing private key cannot be recovered, plan an explicit consent-based backup/activation migration to a new signing key; do not tell users to uninstall their current app until migration has been tested.
