---
id: T02
parent: S02
milestone: M002
provides:
  - Poster route at GET /orangepiller/poster/{arrangement_id} (unauthenticated)
  - Print-optimized poster template with merchant name and large QR code
  - 3 tests covering valid, missing, and no-tpos-url cases
key_files:
  - orangepiller/views.py
  - orangepiller/templates/orangepiller/poster.html
  - tests/extensions/orangepiller/test_poster_route.py
key_decisions:
  - Used {% raw %} wrapper for Vue interpolation in poster template to prevent Jinja interpretation (same pattern as T01)
  - Registered lnbits-qrcode component explicitly on Vue app since poster page doesn't use LNbits.common.VueApp
  - Merchant name falls back to "Merchant" when arrangement.merchant_name is None
patterns_established:
  - Unauthenticated view route pattern with CRUD fetch + HTTPException(404) guard
  - Print template pattern using print.html base with @media print CSS and .print-hide class
observability_surfaces:
  - GET /orangepiller/poster/{bad-id} returns HTTP 404 — verifiable via curl or network tab
  - window.app._instance.data.tposUrl and merchantName inspectable in browser console on poster page
  - No structured logs added — failures surface as HTTP 404 status codes
duration: 10m
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T02: Add poster route and print-optimized template

**Added unauthenticated poster route and print-optimized template with merchant name, large QR code, and print CSS.**

## What Happened

Added `GET /poster/{arrangement_id}` route to `views.py` — unauthenticated (no `check_user_exists` dependency), fetches arrangement via `get_arrangement()`, returns 404 if arrangement not found or `tpos_url` is None, renders poster template with `merchant_name` (fallback "Merchant"), `tpos_url`, and `arrangement_id`.

Created `poster.html` extending `print.html` with: merchant name heading (text-h3), "Pay with Bitcoin ⚡" subtitle, `<lnbits-qrcode>` at large size with `:show-buttons="false"`, "Print this page" button (hidden in print via `.print-hide`), and "Powered by LNbits" footer. Vue app reads data from Jinja-injected `window.poster_data` script block. `@media print` CSS hides non-essential elements and removes margins.

Created 3 tests in `test_poster_route.py`: valid arrangement returns 200 with merchant name and qrcode in body, missing arrangement returns 404, arrangement with `tpos_url=None` returns 404.

## Verification

- `pytest tests/extensions/orangepiller/test_poster_route.py -v` — 3/3 passed
- `pytest tests/extensions/orangepiller/ -v` — 32/32 passed (0 regressions)
- `grep 'print.html' poster.html` — confirms extends print.html
- `grep 'lnbits-qrcode' poster.html` — confirms QR component present
- `grep -c` template inspection — index.html:13, index.js:4 for tpos/qrcode/credentials/poster terms
- Poster route has no `check_user_exists` dependency (verified via grep)

### Slice-level Verification (all pass — this is the final task of S02)

1. ✅ Poster route tests pass (3/3)
2. ✅ Template inspection confirms all dashboard elements wired
3. ✅ Poster extends `print.html` and contains `<lnbits-qrcode>`
4. ✅ Full suite: 32 tests pass (29 existing + 3 new)

## Diagnostics

- `GET /orangepiller/poster/{bad-id}` → HTTP 404
- `GET /orangepiller/poster/{valid-id}` → 200 with merchant name + QR code
- Browser console: `window.app._instance.data.tposUrl` and `merchantName` on poster page
- No new structured logs — read-only view, failures are HTTP status codes

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `orangepiller/views.py` — Added poster route with arrangement fetch, 404 guard, and template rendering
- `orangepiller/templates/orangepiller/poster.html` — New print-optimized poster template (~70 lines)
- `tests/extensions/orangepiller/test_poster_route.py` — New test file with 3 tests
- `.gsd/milestones/M002/slices/S02/tasks/T02-PLAN.md` — Added Observability Impact section (pre-flight fix)
- `.gsd/milestones/M002/slices/S02/S02-PLAN.md` — Marked T02 as [x]
