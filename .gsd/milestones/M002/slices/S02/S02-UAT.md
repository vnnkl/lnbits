# S02: Dashboards, QR codes & printable poster — UAT

**Milestone:** M002
**Written:** 2026-03-16

## UAT Type

- UAT mode: mixed (artifact-driven for poster route + live-runtime for dashboard interaction + human-experience for print quality)
- Why this mode is sufficient: Dashboard columns and QR dialogs require visual inspection in a running instance. Poster print quality requires human judgment. Route contract behavior already proven by automated tests.

## Preconditions

- LNbits instance running with orangepiller extension installed
- TPoS extension installed (for full path testing)
- At least one arrangement created via `POST /orangepiller/api/v1/arrangements` with TPoS provisioning (tpos_url populated)
- At least one arrangement created **without** TPoS (tpos_url is null) — either by running without TPoS installed, or by having a pre-S01 arrangement
- Orange piller logged in with their account

## Smoke Test

Open the orange piller dashboard at `/orangepiller` → the arrangements table should show a "Merchant Name" column, TPoS link with QR icon, credentials copy button, and poster link. If any of these are missing, stop — S02 is broken.

## Test Cases

### 1. Orange piller table — TPoS columns visible

1. Log in as the orange piller
2. Navigate to `/orangepiller`
3. Locate an arrangement with a TPoS terminal provisioned
4. **Expected:** Row shows:
   - Merchant name in its own column
   - TPoS link (external link icon) that opens the TPoS page in a new tab
   - QR code icon button
   - Print/poster icon button
   - Merchant credentials (truncated URL) with a copy icon button

### 2. QR dialog opens with scannable QR code

1. On the orange piller dashboard, click the QR code icon on an arrangement row with TPoS
2. **Expected:** A Quasar dialog opens containing a QR code rendered by `<lnbits-qrcode>`
3. Scan the QR code with a phone camera or QR scanner app
4. **Expected:** QR resolves to the TPoS shareable URL (same as the TPoS link in the table)
5. Close the dialog
6. **Expected:** Dialog closes cleanly, no console errors

### 3. Credentials copy button works

1. On the orange piller dashboard, click the copy button next to merchant credentials on an arrangement row
2. **Expected:** Clipboard contains the merchant login URL (format: `https://{host}/wallet?usr={user_id}`)
3. Open the copied URL in a browser
4. **Expected:** Opens the merchant's LNbits wallet dashboard

### 4. Null TPoS arrangement shows "No TPoS" chip

1. On the orange piller dashboard, locate an arrangement without TPoS provisioning (tpos_url is null)
2. **Expected:** The TPoS column shows a grey "No TPoS" chip instead of links/icons
3. **Expected:** No broken links, no QR icon, no poster link for this row

### 5. Merchant table — TPoS link and QR visible

1. Log in as the merchant (use the credentials URL from the orange piller dashboard)
2. Navigate to `/orangepiller`
3. **Expected:** Merchant sees their arrangement with TPoS link (external icon) and QR icon button
4. Click the QR icon
5. **Expected:** Dialog opens with QR code pointing to the merchant's TPoS URL
6. **Expected:** No poster link, no credentials column visible to the merchant

### 6. Poster page renders correctly

1. On the orange piller dashboard, click the poster/print icon for an arrangement with TPoS
2. **Expected:** New page opens at `/orangepiller/poster/{arrangement_id}`
3. **Expected:** Page shows:
   - Merchant name as a heading (or "Merchant" if name was not set)
   - "Pay with Bitcoin ⚡" subtitle
   - Large QR code (rendered by `<lnbits-qrcode>`)
   - "Print this page" button
   - "Powered by LNbits" footer

### 7. Poster prints cleanly

1. On the poster page, click "Print this page" (or use Ctrl/Cmd+P)
2. **Expected:** Print preview shows:
   - Merchant name and QR code prominently
   - "Print this page" button is NOT visible in print preview
   - No browser chrome, navigation bars, or extraneous elements
   - Clean margins suitable for an A4/Letter page
3. If a printer is available, print and verify QR is scannable from paper

### 8. Poster page — direct URL access (no auth required)

1. Copy the poster URL: `/orangepiller/poster/{arrangement_id}`
2. Open it in an incognito/private browser window (no LNbits session)
3. **Expected:** Poster renders with merchant name and QR — no login redirect

## Edge Cases

### Missing arrangement returns 404

1. Navigate to `/orangepiller/poster/nonexistent-id-12345`
2. **Expected:** HTTP 404 response (standard LNbits error page)

### Arrangement without TPoS returns 404 on poster

1. Find the arrangement_id of an arrangement with no TPoS (tpos_url is null)
2. Navigate to `/orangepiller/poster/{that_arrangement_id}`
3. **Expected:** HTTP 404 response — poster requires a TPoS URL to render the QR code

### QR dialog with very long TPoS URL

1. If possible, create an arrangement where the TPoS URL is unusually long
2. Open the QR dialog
3. **Expected:** QR code renders (may be denser but still scannable); dialog doesn't overflow

## Failure Signals

- Missing columns in either table → JS error in console or columns array misconfigured
- QR dialog doesn't open → `showQr()` method not wired or `showQrDialog` state broken
- "No TPoS" chip not showing → `v-if="row.tpos_url"` guard missing
- Poster page shows raw `{{ }}` text → `{% raw %}` wrapper missing in template
- Poster page shows blank QR → `lnbits-qrcode` component not registered on poster Vue app
- Copy button does nothing → `copyText()` method not available or credentials field null
- 500 error on poster route → `get_arrangement()` import or route registration issue

## Requirements Proved By This UAT

- R104 — TPoS link and QR on both dashboards: proven by tests 1, 2, 4, 5
- R105 — Printable merchant poster with QR code: proven by tests 6, 7, 8
- R106 — Merchant credentials surfaced in UI: proven by test 3

## Not Proven By This UAT

- QR scannability at various print sizes and printer qualities (requires real-world testing with multiple devices)
- Poster rendering on different paper sizes (A4, Letter, etc.)
- Dashboard behavior under slow network conditions
- TPoS payment flow end-to-end (TPoS functionality is TPoS extension's responsibility)

## Notes for Tester

- The poster page uses a standalone Vue app, not the full LNbits Vue setup. If the QR component doesn't render, check the browser console for component registration errors.
- Merchant credentials are a `/wallet?usr={id}` URL — this is standard LNbits auth, not a password. Treat it as sensitive (anyone with the URL can access the wallet).
- The "No TPoS" chip is expected for pre-S01 arrangements or arrangements created when TPoS wasn't installed — it's not a bug.
- Print quality depends heavily on the browser's print engine. Chrome/Chromium generally produces the best results with `@media print` CSS.
