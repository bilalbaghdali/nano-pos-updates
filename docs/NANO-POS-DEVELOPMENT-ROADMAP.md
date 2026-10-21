# NANO POS — Staged development roadmap (baseline v1.0.97)

All updates are constructed from the SHA-256-verified **latest official ASAR**. Do not revert to v1.0.94.

| Release | Scope | Status | Safety gate |
|---|---|---|---|
| 1.0.94 | Application stability, verified backup, updater rollback | Released | Windows update/rollback regressions |
| 1.0.95 | Fast checkout, invoice edit protections | Released | Duplicate submission and edit regression checks |
| 1.0.96 | Durable cross-device sync ledger | Released | Concurrent phone/PC and restart checks |
| 1.0.97 | Automatic in-app updates | Released | Linux and Windows update simulations |
| **1.0.98** | Inventory intelligence: forecast in existing low-stock list, suggested purchase quantities and days of stock coverage | Released | Read-only calculations; unchanged DB and activation; Linux & Windows tests passed |
| **1.0.99** | UI navigation/performance, dashboard data accuracy and audit trail | Planned | UI and existing data regression tests, audit persistency checks |
| Later | Multi-device stocktake workflows and advanced recovery safeguards | Planned, separately gated | Real-device/staging tests before production release |

## Non-negotiable release gates

1. Verify official source patch ZIP SHA-256 and embedded app.asar SHA-256 against the current published update manifest.
2. Avoid destructive database migrations. Preserve shop data, customers, debts, sales, settings, device IDs, activation/licensing, and backups.
3. Make changes in focused patches. Fail if expected source markers or hashes have changed.
4. Run syntax/static checks and behavior regression suites on Linux **and** Windows before publishing.
5. Publish the release asset first, then publish an auto-update manifest containing actual asset SHA-256.
6. Never label the whole program as end-to-end tested: real cashier devices and all accounting side effects require separate staging verification.
7. Preserve the in-app auto-update installation behavior, including deferral during active sales.
8. Document changes in Arabic, French and English; do not advertise as implemented any features not validated.

## Next-step policy

Build 1.0.98 from the official 1.0.97; **no reversion to 1.0.94**.
Prioritize safe, read-only inventory recommendations based on existing records. Do not automatically modify stock, sales, purchasing, or supplier records.
