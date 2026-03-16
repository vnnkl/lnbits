---
id: T01
parent: S02
milestone: M002
provides:
  - TPoS link + QR + poster columns in orange piller dashboard table
  - TPoS link + QR column in merchant dashboard table
  - QR dialog with lnbits-qrcode component
  - Merchant credentials copy button
  - Merchant name column
key_files:
  - orangepiller/static/js/index.js
  - orangepiller/templates/orangepiller/index.html
key_decisions:
  - Used `type="a"` with `:href` on q-btn for TPoS and poster links (native anchor behavior, opens in new tab)
  - Wrapped credentials display in {% raw %}{% endraw %} to prevent Jinja from interpreting Vue interpolation
  - QR dialog is shared between both tables via single showQr() method
patterns_established:
  - body-cell slot pattern for custom column rendering (tpos, merchant_credentials)
  - Shared dialog state pattern (showQrDialog + qrDialogUrl) for reuse across tables
observability_surfaces:
  - Browser console: showQrDialog and qrDialogUrl inspectable via Vue devtools / window.app._instance.data
  - Column counts verifiable: columns=12, merchantColumns=8
  - No TPoS chip visible when tpos_url is null
duration: 15m
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T01: Add TPoS, QR, credentials, and poster columns to both dashboards

**Wired TPoS links, QR dialog, credentials copy, poster links, and merchant name into both dashboard tables with null-safe guards.**

## What Happened

Added three new columns to the orange piller `columns` array (`merchant_name`, `tpos`, `merchant_credentials`) and one to `merchantColumns` (`tpos`). Column counts went from 9→12 and 7→8 respectively.

In `index.html`, added body-cell slots for:
- **tpos** (orange piller table): open_in_new link, qr_code_2 button calling `showQr()`, print button linking to `/orangepiller/poster/{id}`. Falls back to grey "No TPoS" chip when `tpos_url` is null.
- **merchant_credentials** (orange piller table): truncated text + copy button calling `copyText()`. Shows dash when null.
- **tpos** (merchant table): same link + QR pattern, minus poster and credentials.

Added shared QR dialog with `<lnbits-qrcode :value="qrDialogUrl">` after the forgive dialog.

Updated completion toast to use `merchant_name || merchant_wallet` for the label.

## Verification

- `grep -c` confirms all 6 key terms present in both files (JS: 9 hits, HTML: 14 hits)
- Column counts verified programmatically: columns=12, merchantColumns=8
- Body-cell slot names match column `name` fields in both tables
- All 29 existing orangepiller tests pass (0.56s)
- Slice-level template inspection grep passes

## Diagnostics

- `showQrDialog` / `qrDialogUrl` inspectable in browser console via Vue devtools
- "No TPoS" grey chip is the visual signal for arrangements without TPoS provisioning
- No new network requests or console logging added — credentials stay client-side only

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `orangepiller/static/js/index.js` — Added QR dialog state, showQr() method, 3 columns to columns array, 1 to merchantColumns, updated completion toast label
- `orangepiller/templates/orangepiller/index.html` — Added tpos + merchant_credentials body-cell slots in orange piller table, tpos slot in merchant table, QR dialog markup
- `.gsd/milestones/M002/slices/S02/S02-PLAN.md` — Added Observability / Diagnostics section
- `.gsd/milestones/M002/slices/S02/tasks/T01-PLAN.md` — Added Observability Impact section
