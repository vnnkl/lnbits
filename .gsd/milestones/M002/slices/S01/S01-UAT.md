# S01: TPoS integration + extended onboarding — UAT

**Milestone:** M002
**Written:** 2026-03-16

## UAT Type

- UAT mode: live-runtime
- Why this mode is sufficient: The contract tests prove API shape and mock-level behavior, but TPoS auto-provisioning involves a real cross-extension HTTP call that can only be fully validated on a running LNbits instance with the TPoS extension installed.

## Preconditions

1. LNbits instance running locally (e.g. `python -m uvicorn lnbits.app:create_app --factory --reload`)
2. Orange Piller extension installed and enabled
3. TPoS extension installed and enabled (for happy-path tests)
4. An orange piller user account with a funded wallet (at least 1 sat for API auth)
5. Admin key of the orange piller's wallet available for API requests
6. Base URL known (e.g. `http://localhost:5000`)

## Smoke Test

```bash
curl -X POST http://localhost:5000/orangepiller/api/v1/arrangements \
  -H "X-Api-Key: <orange_piller_adminkey>" \
  -H "Content-Type: application/json" \
  -d '{"total_debt_sats": 10000, "reroute_percent": 10, "merchant_name": "Café Bitcoin"}'
```

**Expected:** 201 response with `tpos_id`, `tpos_url`, `merchant_credentials` populated (if TPoS installed) or `tpos_id: null` with `warning` present (if TPoS not installed).

## Test Cases

### 1. Happy path: TPoS auto-provisioning

1. Ensure TPoS extension is installed and enabled
2. POST to `/orangepiller/api/v1/arrangements`:
   ```json
   {
     "total_debt_sats": 50000,
     "reroute_percent": 15,
     "merchant_name": "Pizza Palace",
     "currency": "EUR",
     "tip_options": "[5, 10, 15]",
     "tax_default": 19.0,
     "tax_inclusive": true,
     "business_name": "Pizza Palace GmbH",
     "business_address": "123 Main St",
     "business_vat_id": "DE123456789"
   }
   ```
3. **Expected response includes:**
   - `tpos_id` — non-null string (the created TPoS terminal ID)
   - `tpos_url` — URL containing `/tpos/{tpos_id}`
   - `merchant_credentials` — URL containing `/wallet?usr=`
   - `merchant_name` — `"Pizza Palace"`
   - No `warning` field (or `warning: null`)
4. Open `tpos_url` in a browser
5. **Expected:** TPoS payment terminal page loads with "Pizza Palace" as the terminal name, EUR currency, and tip options visible

### 2. Merchant credentials work

1. From test case 1, copy the `merchant_credentials` URL
2. Open it in a browser (or incognito window)
3. **Expected:** LNbits wallet dashboard loads for the merchant account
4. Navigate to the Orange Piller extension in the merchant's view
5. **Expected:** Merchant sees their arrangement details (debt: 50000 sats, reroute: 15%, status: active)

### 3. Graceful degradation: TPoS not installed

1. Disable or uninstall the TPoS extension from the LNbits admin
2. POST to `/orangepiller/api/v1/arrangements`:
   ```json
   {
     "total_debt_sats": 25000,
     "reroute_percent": 20,
     "merchant_name": "Book Shop"
   }
   ```
3. **Expected response includes:**
   - `tpos_id` — `null`
   - `tpos_url` — `null`
   - `merchant_credentials` — non-null URL containing `/wallet?usr=`
   - `warning` — contains "not installed"
4. **Expected:** Arrangement is fully created (GET returns it), only TPoS fields are missing

### 4. Extended fields persist and return via GET

1. Create an arrangement with all extended fields (as in test case 1)
2. GET `/orangepiller/api/v1/arrangements` with orange piller's admin key
3. **Expected:** The arrangement in the list includes `tpos_id`, `tpos_url`, `merchant_name`, `merchant_credentials`
4. GET `/orangepiller/api/v1/merchant/arrangements` with the merchant's admin key
5. **Expected:** Same fields present in merchant view

### 5. TPoS terminal generates Lightning invoices

1. From test case 1, open the `tpos_url` in a browser
2. Enter an amount (e.g. 100 sats) on the TPoS keypad
3. Tap "Pay" / generate invoice
4. **Expected:** A Lightning invoice (BOLT11) is generated and displayed as a QR code
5. Pay the invoice from another wallet
6. **Expected:** Payment succeeds; the rerouting engine activates (15% of 100 sats = 15 sats rerouted to orange piller)

## Edge Cases

### Minimal fields — only required parameters

1. POST with only `total_debt_sats` and `reroute_percent` (no merchant_name, currency, etc.):
   ```json
   {"total_debt_sats": 5000, "reroute_percent": 10}
   ```
2. **Expected:** Arrangement created. `merchant_name` is null. TPoS terminal created with default name "Terminal" and currency "sat". No errors.

### TPoS HTTP failure simulation

1. If possible, configure LNbits to use an unreachable internal URL (modify `lnbits_baseurl` in settings) or temporarily break TPoS routes
2. POST to create an arrangement
3. **Expected:** Arrangement created with `tpos_id: null` and `warning` containing the failure message (e.g. connection error). No 500 error.

### Multiple arrangements with TPoS

1. Create 3 arrangements with different merchant names and TPoS settings
2. GET `/orangepiller/api/v1/arrangements`
3. **Expected:** All 3 arrangements returned, each with their own `tpos_id` and `tpos_url` (3 distinct TPoS terminals created)

## Failure Signals

- 500 error on POST when TPoS is not installed → graceful degradation broken
- `tpos_url` populated but URL returns 404 → TPoS terminal creation succeeded but ID mapping broken
- `merchant_credentials` URL returns "user not found" → user creation or credential construction broken
- `tpos_id` is null when TPoS is installed and no `warning` present → TPoS detection or httpx call silently failing
- Existing M001 arrangements broken or missing fields → migration or model change caused regression

## Requirements Proved By This UAT

- R101 — TPoS auto-provisioning: test cases 1 and 5 prove terminal is created and functional
- R102 — Extended onboarding form: test cases 1 and edge case 1 prove all fields accepted
- R103 — Graceful degradation: test case 3 proves arrangement succeeds without TPoS
- R106 — Merchant credentials: test case 2 proves login URL works

## Not Proven By This UAT

- R104 (TPoS link and QR on dashboards) — deferred to S02
- R105 (Printable merchant poster) — deferred to S02
- R106 dashboard display — credential URL is proven functional, but dashboard rendering is S02

## Notes for Tester

- The `merchant_credentials` URL uses LNbits user-id auth (`/wallet?usr={id}`). This is standard LNbits behavior — not a security concern in the context of local/self-hosted instances.
- The `warning` field is **response-only** — it appears on POST responses but NOT on subsequent GET calls. This is by design (the warning is about provisioning status at creation time, not persistent state).
- If testing on a fresh LNbits instance, you'll need to fund the orange piller's wallet first. Use the LNbits funding source or admin tools to add sats.
- TPoS settings (currency, tip_options, tax) are passed through to TPoS — verify them by inspecting the TPoS admin page for the merchant's account, not just the TPoS payment page.
