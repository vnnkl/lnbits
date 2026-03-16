---
id: S02
parent: M002
milestone: M002
provides:
  - TPoS link + QR dialog + poster link columns in orange piller dashboard table
  - TPoS link + QR dialog column in merchant dashboard table
  - Merchant credentials copy button in orange piller dashboard
  - Merchant name column in orange piller dashboard
  - Unauthenticated poster route at GET /orangepiller/poster/{arrangement_id}
  - Print-optimized poster template with merchant name and large QR code
requires:
  - slice: S01
    provides: Arrangement model with tpos_id, tpos_url, merchant_name, merchant_credentials fields; get_arrangement() CRUD
affects: []
key_files:
  - orangepiller/static/js/index.js
  - orangepiller/templates/orangepiller/index.html
  - orangepiller/views.py
  - orangepiller/templates/orangepiller/poster.html
  - tests/extensions/orangepiller/test_poster_route.py
key_decisions:
  - Used `type="a"` with `:href` on q-btn for TPoS and poster links (native anchor behavior, opens in new tab)
  - Wrapped credentials display in {% raw %}{% endraw %} to prevent Jinja from interpreting Vue interpolation
  - QR dialog shared between both tables via single showQr() method and shared state (showQrDialog + qrDialogUrl)
  - Poster route is unauthenticated — public shareable URL; returns 404 for missing arrangement or null tpos_url
  - Registered lnbits-qrcode component explicitly on poster Vue app since poster page doesn't use LNbits.common.VueApp
  - Merchant name falls back to "Merchant" when arrangement.merchant_name is None
patterns_established:
  - body-cell slot pattern for custom column rendering (tpos, merchant_credentials)
  - Shared dialog state pattern (showQrDialog + qrDialogUrl) for reuse across tables
  - Unauthenticated view route pattern with CRUD fetch + HTTPException(404) guard
  - Print template pattern using print.html base with @media print CSS and .print-hide class
observability_surfaces:
  - Browser console: showQrDialog and qrDialogUrl inspectable via Vue devtools
  - Column counts verifiable: columns=12, merchantColumns=8
  - "No TPoS" grey chip visible when tpos_url is null
  - GET /orangepiller/poster/{bad-id} returns HTTP 404
  - window.app._instance.data.tposUrl and merchantName inspectable on poster page
drill_down_paths:
  - .gsd/milestones/M002/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/milestones/M002/slices/S02/tasks/T02-SUMMARY.md
duration: 25m
verification_result: passed
completed_at: 2026-03-16
---

# S02: Dashboards, QR codes & printable poster

**Both dashboards surface TPoS links with QR dialogs, merchant credentials with copy buttons, poster links, and a dedicated print-optimized poster route renders merchant name + large QR code at a public URL.**

## What Happened

**T01 — Dashboard columns and QR dialog.** Added three new columns to the orange piller table (`merchant_name`, `tpos`, `merchant_credentials`) and one to the merchant table (`tpos`). Column counts went from 9→12 and 7→8. The `tpos` column renders an open-in-new-tab link, a QR icon button that opens a shared `<q-dialog>` with `<lnbits-qrcode>`, and a print icon linking to `/orangepiller/poster/{id}`. The `merchant_credentials` column shows a truncated URL with a copy button via `copyText()`. All TPoS UI is guarded with `v-if="row.tpos_url"` — null values show a grey "No TPoS" chip. Vue interpolation in Jinja templates wrapped in `{% raw %}` blocks.

**T02 — Poster route and template.** Added `GET /poster/{arrangement_id}` to `views.py` as an unauthenticated route (no `check_user_exists` dependency). It fetches the arrangement via `get_arrangement()`, returns 404 if not found or `tpos_url` is None, and renders `poster.html`. The poster template extends `print.html` with merchant name heading, "Pay with Bitcoin ⚡" subtitle, large `<lnbits-qrcode>` (buttons hidden), a "Print this page" button (hidden in print via `.print-hide`), and "Powered by LNbits" footer. Three tests verify the 200/404 behavior.

## Verification

- `pytest tests/extensions/orangepiller/test_poster_route.py -v` — 3/3 passed (valid arrangement → 200, missing → 404, no tpos_url → 404)
- `pytest tests/extensions/orangepiller/ -v` — 32/32 passed (29 existing + 3 new, 0 regressions)
- Template inspection: `grep -c` confirms all key terms (`tpos_url`, `lnbits-qrcode`, `merchant_credentials`, `showQrDialog`) present in both JS (6 hits) and HTML (12 hits)
- Poster template extends `print.html` and contains `<lnbits-qrcode>` component
- Column counts verified: columns=12, merchantColumns=8

## Requirements Advanced

- R104 — TPoS link and QR code now present on both dashboards with null-safe guards
- R105 — Printable poster route serves merchant name + QR at public URL with print-optimized CSS
- R106 — Merchant credentials surfaced with copy button on orange piller dashboard (UI side; API side validated in S01)

## Requirements Validated

- R104 — Dashboard columns wired with body-cell slots; QR dialog uses `<lnbits-qrcode>`; null guard shows "No TPoS" chip; template inspection grep passes
- R105 — Poster route at `/orangepiller/poster/{id}` returns 200 with merchant name + qrcode for valid arrangements, 404 for missing/no-tpos; extends `print.html`; 3 contract tests pass
- R106 — Merchant credentials displayed truncated with copy button in dashboard table; validated in S01 (API) + S02 (UI) — full chain complete

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

None.

## Known Limitations

- QR scannability at print resolution not verified (deferred to UAT — requires physical print test)
- Poster visual design quality not verified (deferred to UAT — requires human judgment)
- Dashboard column rendering not visually verified (deferred to UAT — contract tests + template inspection only)

## Follow-ups

- none — S02 is the final slice for M002

## Files Created/Modified

- `orangepiller/static/js/index.js` — Added QR dialog state, showQr() method, 3 columns to columns array, 1 to merchantColumns, updated completion toast label
- `orangepiller/templates/orangepiller/index.html` — Added tpos + merchant_credentials body-cell slots in both tables, QR dialog markup
- `orangepiller/views.py` — Added poster route with arrangement fetch, 404 guard, and template rendering
- `orangepiller/templates/orangepiller/poster.html` — New print-optimized poster template (~70 lines)
- `tests/extensions/orangepiller/test_poster_route.py` — New test file with 3 contract tests

## Forward Intelligence

### What the next slice should know
- M002 is complete. No downstream slices remain. The next milestone should consume `Arrangement` as a stable model — all fields are now populated and surfaced in both API and UI.

### What's fragile
- `{% raw %}` blocks in Jinja templates — any new Vue interpolation in `index.html` or `poster.html` must be wrapped, or Jinja will silently eat the `{{ }}` expressions at render time.
- `lnbits-qrcode` component registration on poster page — the poster doesn't use `LNbits.common.VueApp`, so the component must be manually registered. If LNbits changes how components are exported, the poster will break silently.

### Authoritative diagnostics
- `pytest tests/extensions/orangepiller/ -v` — 32 tests in <1s, covers all M001+M002 contract verification
- `grep -c 'tpos_url\|lnbits-qrcode\|merchant_credentials\|showQrDialog'` on JS and HTML files — confirms dashboard wiring without needing a running server

### What assumptions changed
- No assumptions changed — S02 consumed exactly the S01 boundary outputs as documented in the plan.
