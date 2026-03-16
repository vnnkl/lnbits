---
estimated_steps: 5
estimated_files: 3
---

# T02: Add poster route and print-optimized template

**Slice:** S02 — Dashboards, QR codes & printable poster
**Milestone:** M002

## Description

Create the printable poster page: a new view route at `GET /orangepiller/poster/{arrangement_id}` (unauthenticated) that fetches the arrangement and renders a clean, print-optimized template with the merchant's name and a large QR code pointing to their TPoS payment page. Write tests proving the route's 200/404 behavior.

## Steps

1. In `views.py`, add `GET /poster/{arrangement_id}` route on `orangepiller_ext_generic`. Import `get_arrangement` from crud. No auth dependency. Fetch arrangement — if `None` or `arrangement.tpos_url is None`, raise `HTTPException(404)`. Otherwise render `orangepiller/poster.html` with arrangement data as context (dict with `merchant_name`, `tpos_url`, `arrangement_id`).

2. Create `orangepiller/templates/orangepiller/poster.html` extending `print.html`. In `{% block styles %}`, add `@media print` CSS: hide non-essential elements, maximize QR size, center content, no margins. In `{% block page %}`, render: merchant name as large `<div class="text-h3">`, "Pay with Bitcoin ⚡" subtitle, `<lnbits-qrcode>` component at large size with `:show-buttons="false"`. In `{% block scripts %}`, create a minimal Vue app that reads arrangement data from a Jinja-injected `<script>` block: `window.poster_data = {{ poster_data | tojson | safe }}`, then `window.app = Vue.createApp({ data() { return { tposUrl: window.poster_data.tpos_url } } })`.

3. In `poster.html`, add a small footer: "Powered by LNbits" with subtle styling. Add a "Print this page" button visible on screen but hidden in print via `class="print-hide"`.

4. Create `tests/extensions/orangepiller/test_poster_route.py` with tests:
   - `test_poster_route_valid_arrangement` — mock `get_arrangement` to return an arrangement with `tpos_url` set, assert response status 200 and response contains the merchant name and "qrcode" (from the template)
   - `test_poster_route_missing_arrangement` — mock returns `None`, assert 404
   - `test_poster_route_no_tpos_url` — mock returns arrangement with `tpos_url=None`, assert 404

5. Run full test suite: `pytest tests/extensions/orangepiller/ -v` — all 29+ tests pass with no regressions.

## Must-Haves

- [ ] Poster route is unauthenticated (no `check_user_exists` dependency)
- [ ] 404 when arrangement not found or `tpos_url` is None
- [ ] Template extends `print.html` (not `base.html`)
- [ ] QR uses `<lnbits-qrcode>` component with `show-buttons="false"`
- [ ] Print CSS hides screen-only elements
- [ ] 3 tests cover valid, missing, and no-tpos cases

## Verification

- `pytest tests/extensions/orangepiller/test_poster_route.py -v` — 3 tests pass
- `pytest tests/extensions/orangepiller/ -v` — 29+ tests pass (no regressions)
- `grep 'print.html' orangepiller/templates/orangepiller/poster.html` — confirms base template
- `grep 'lnbits-qrcode' orangepiller/templates/orangepiller/poster.html` — confirms QR component

## Inputs

- `orangepiller/views.py` — existing router and template_renderer pattern
- `orangepiller/crud.py` — `get_arrangement(arrangement_id)` returns `Optional[Arrangement]`
- `lnbits/templates/print.html` — base print template with Quasar/Vue/components, `@page A4` CSS
- S01 Forward Intelligence: `tpos_url` null when TPoS absent; `merchant_name` may be null (use fallback "Merchant")

## Observability Impact

- **Poster route 404 diagnostics:** `GET /orangepiller/poster/{bad-id}` returns HTTP 404 — verifiable via `curl -s -o /dev/null -w '%{http_code}'` or the browser network tab.
- **Poster route 200 verification:** `GET /orangepiller/poster/{valid-id}` returns HTML containing the merchant name and `lnbits-qrcode` component — verifiable via `curl -s | grep`.
- **Vue data inspection:** `window.app._instance.data.tposUrl` and `merchantName` are inspectable in browser console on the poster page.
- **No new structured logs:** The poster route is a simple read-only view; failures surface as HTTP 404 status codes, not log entries.

## Expected Output

- `orangepiller/views.py` — one new route added
- `orangepiller/templates/orangepiller/poster.html` — new file, ~60 lines
- `tests/extensions/orangepiller/test_poster_route.py` — new file, 3 tests
