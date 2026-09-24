# nano-pos-updates

Public **distribution-only** repository for NANO POS Windows partial updates.

- Releases contain the signed `nano-pos-update.json` and changed application files only.
- A cumulative manifest points unchanged files to their existing release assets; installed clients compare SHA-256 and download only changed files.
- Source code and signing secrets stay in the private repository `bilalbaghdali/nanopos`, branch `desktop-stable-v8`.
- GitHub Actions on that private branch publishes a new release only if tests pass and application files actually changed.
- Never upload activation secrets, signing keys, customer databases, backup files or private code here.

Current publication automation requires the owner to sync the desktop source to the private branch and configure its Actions secrets once.
