# S02: Dashboards, QR codes & printable poster

**Goal:** Both dashboards surface TPoS links with QR codes, merchant credentials are copyable on the orange piller dashboard, and a printable poster page renders at `/orangepiller/poster/{arrangement_id}`.
**Demo:** Orange piller opens dashboard → sees merchant name, TPoS link with QR icon, credentials copy button, and "Print poster" link per arrangement. Merchant sees their TPoS link + QR. Poster page renders a clean, print-optimized page with merchant name and large QR code.

## Must-Haves

- Orange piller table shows `merchant_name`, TPoS link + QR dialog button, merchant credentials copy button, poster link — all guarded against null `tpos_url`
- Merchant table shows TPoS link + QR dialog button — guarded against null `tpos_url`
- QR dialog uses existing `<lnbits-qrcode>` component (no custom QR rendering)
- Poster route at `GET /orangepiller/poster/{arrangement_id}` — unauthenticated, 404 on missing arrangement or null `tpos_url`
- Poster template extends `print.html` — merchant name, large QR, print-optimized CSS

## Proof Level

- This slice proves: contract (template output and route behavior)
- Real runtime required: no (template inspection + route test sufficient; visual QR scannability deferred to UAT)
- Human/UAT required: yes (poster print quality, QR scannability at print resolution)

## Verification

- `pytest tests/extensions/orangepiller/test_poster_route.py -v` — poster route returns HTML for valid arrangement, 404 for missing/no-tpos arrangements
- Template inspection: `grep -c 'tpos_url\|lnbits-qrcode\|merchant_credentials\|poster' orangepiller/templates/orangepiller/index.html orangepiller/static/js/index.js` confirms all dashboard elements wired
- Poster template extends `print.html` and contains `<lnbits-qrcode>` component
- All 29 existing tests still pass: `pytest tests/extensions/orangepiller/ -v`

## Integration Closure

- Upstream surfaces consumed: `Arrangement.tpos_url`, `Arrangement.merchant_name`, `Arrangement.merchant_credentials`, `Arrangement.tpos_id` from S01; `get_arrangement()` CRUD; `<lnbits-qrcode>` component; `print.html` base template
- New wiring introduced in this slice: poster view route registered on `orangepiller_ext_generic` router; poster template in extension templates directory
- What remains before the milestone is truly usable end-to-end: nothing — S02 is the final slice for M002

## Tasks

- [x] **T01: Add TPoS, QR, credentials, and poster columns to both dashboards** `est:45m`
  - Why: R104 (TPoS link + QR on dashboards) and R106 (merchant credentials surfaced in UI) — the core dashboard visibility that makes TPoS and credentials accessible to both parties
  - Files: `orangepiller/static/js/index.js`, `orangepiller/templates/orangepiller/index.html`
  - Do: Add `merchant_name`, `tpos` (custom slot with link + QR icon button + poster link), `merchant_credentials` (copy button) columns to orange piller table. Add `tpos` column to merchant table. Add `showQrDialog`/`qrDialogUrl` data fields and `<q-dialog>` with `<lnbits-qrcode>`. Guard all TPoS UI with `v-if="row.tpos_url"` — show "No TPoS" chip otherwise. Use existing patterns: `this.utils.copyText()` for clipboard, Quasar dialog for QR, body-cell slots for custom rendering.
  - Verify: `grep -c 'tpos_url\|lnbits-qrcode\|merchant_credentials\|showQrDialog' orangepiller/static/js/index.js orangepiller/templates/orangepiller/index.html` — all terms present in both files
  - Done when: Both tables render new columns; QR dialog opens with `<lnbits-qrcode>`; null `tpos_url` shows informative chip; credentials have copy button; poster link present

- [x] **T02: Add poster route and print-optimized template** `est:30m`
  - Why: R105 (printable merchant poster) — the physical artifact the orange piller gives the merchant
  - Files: `orangepiller/views.py`, `orangepiller/templates/orangepiller/poster.html`, `tests/extensions/orangepiller/test_poster_route.py`
  - Do: Add `GET /poster/{arrangement_id}` route to views.py — unauthenticated, fetches arrangement via `get_arrangement()`, returns 404 if not found or `tpos_url` is None, passes arrangement data as template context. Create `poster.html` extending `print.html` with: merchant name heading, "Pay with Bitcoin ⚡" subtitle, `<lnbits-qrcode :value="tposUrl" :show-buttons="false">` at large size, LNbits branding footer. Vue app reads arrangement data from Jinja-injected `<script>` block. Add `@media print` CSS for clean output. Write test file verifying route 200/404 behavior.
  - Verify: `pytest tests/extensions/orangepiller/test_poster_route.py -v` — all tests pass; `pytest tests/extensions/orangepiller/ -v` — 29+ tests pass (no regressions)
  - Done when: Poster route serves HTML with QR for valid arrangements, returns 404 for invalid/no-tpos cases, all tests pass

## Observability / Diagnostics

- **Browser console:** QR dialog open/close and `copyText()` calls produce no console errors when functioning correctly. A `TypeError` on `showQr` or `copyText` indicates missing method wiring.
- **Column count verification:** `columns` array length (12) and `merchantColumns` length (8) are inspectable via `window.app._instance.data.columns.length` in the browser console.
- **Poster route 404:** `GET /orangepiller/poster/{bad-id}` returns HTTP 404 with standard LNbits error template — verifiable via curl or network tab.
- **QR dialog state:** `window.app._instance.data.showQrDialog` and `qrDialogUrl` are inspectable in browser console to verify dialog state.
- **No secrets in UI:** `merchant_credentials` is displayed truncated in the table and copied to clipboard; it is never logged to console or included in network requests from the dashboard.

## Files Likely Touched

- `orangepiller/static/js/index.js`
- `orangepiller/templates/orangepiller/index.html`
- `orangepiller/views.py`
- `orangepiller/templates/orangepiller/poster.html` *(new)*
- `tests/extensions/orangepiller/test_poster_route.py` *(new)*
