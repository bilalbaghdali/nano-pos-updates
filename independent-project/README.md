# NANO Commerce — independent development project

This branch preserves the Multi-Commerce concept separately from the original **NANO POS** production update line. **Not published**.

## Separation contract

1. Independent Windows identity: `NANO Commerce.exe`, `com.nanocommerce.desktop`.
2. Independent installation directory and Windows shortcuts.
3. Independent Electron userData folder: `%APPDATA%\\NANO Commerce`.
4. Independent Chromium localStorage origin: local port 4276 instead of 4176.
5. Independent LAN sync port: 4278 instead of 4178. Never connect to another product's inventory automatically.
6. No shared license/activation, trial secrets, activation database, backup directory or installation identifiers.
7. No automatic imports of existing NANO POS business records; require an explicit import with backup and schema checks.
8. No reference to the public NANO POS update manifest in the new app. The new product has **no updater enabled** until a separately owned update feed is created.
9. Build and publish artifacts only under an independent GitHub repository, after naming and license isolation audits. Never upload to `bilalbaghdali/nano-pos-updates`.
10. New functionalities (unit conversions, variants, scale, vehicle VIN, installments) require independent business-logic and migration tests before release.

## Present state

- The NANO POS original application remains **v1.0.91**.
- The original public v1.1.0 Multi-Commerce GitHub Release was changed into a draft (unpublished) and its update manifest rolled back.
- Multi-Commerce screen design and phase-1 code are preserved for migration; **they do not yet constitute an independently installable or securely isolated application**.
- The temporary staging branch in the old repository is **not** a substitute for a dedicated repository. It must not run automatic publishing.
- Next engineering work: create the separate source repository, audit existing absolute paths and update/licensing services, apply independent identity, build an isolated Windows installer, and test side-by-side installation with NANO POS before releasing.

## Safety gate

Do not mark a release ready until a Windows integration test confirms both applications running side by side, completely separate sales/customers/inventory, isolated installation/backup/activation, independent updater, separate ports, and no cross-version updates.
