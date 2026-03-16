# S04: Merchant view + arrangement management — UAT

**Milestone:** M001
**Written:** 2026-03-16

## UAT Type

- UAT mode: mixed (artifact-driven for API + human-experience for UI)
- Why this mode is sufficient: API contracts verified by tests; UI requires visual inspection on a running LNbits instance

## Preconditions

1. LNbits instance running with the orangepiller extension installed
2. At least one orange piller account with an active arrangement (merchant onboarded via `POST /api/v1/onboard`)
3. Know the orange piller's admin key and the merchant's invoice/read key
4. At least one arrangement should have some repaid_sats > 0 (make a payment to the merchant first)

## Smoke Test

Log in as the merchant → open the Orange Piller extension → a "Your Payback Arrangement" section should appear showing the arrangement details with a progress bar.

## Test Cases

### 1. Merchant sees their arrangement

1. Log into LNbits as the merchant user
2. Open the Orange Piller extension
3. Select the merchant's wallet in the wallet dropdown
4. **Expected:** A "Your Payback Arrangement" section appears with a Quasar table showing: total debt (sats), repaid amount, remaining debt, progress bar, reroute percentage, and status ("active")

### 2. Non-merchant wallet sees no merchant section

1. Log into LNbits as the orange piller
2. Open the Orange Piller extension
3. Select the orange piller's wallet
4. **Expected:** No "Your Payback Arrangement" section appears — only the orange piller's dashboard table is visible

### 3. Orange piller edits reroute percentage

1. Log into LNbits as the orange piller
2. Open the Orange Piller extension → see the arrangements table
3. Click the pencil (edit) icon on an active arrangement's row
4. **Expected:** An edit dialog opens showing the current reroute percentage
5. Change the percentage to 50, click Save
6. **Expected:** Dialog closes, table refreshes, the arrangement now shows 50% reroute

### 4. Edit dialog validates percentage range

1. Open the edit dialog on an active arrangement
2. Try entering 0 — **Expected:** Validation error, save disabled or rejected
3. Try entering 101 — **Expected:** Validation error, save disabled or rejected
4. Try entering 75 — **Expected:** Accepted, saves successfully

### 5. Orange piller forgives remaining debt

1. Log into LNbits as the orange piller
2. Click the heart (forgive) icon on an active arrangement
3. **Expected:** A confirmation dialog appears with an "irreversible" warning
4. Confirm the forgiveness
5. **Expected:** Dialog closes, arrangement status changes to "completed", edit and forgive buttons disappear from that row

### 6. Forgiven arrangement visible to merchant

1. After forgiving in test 5, log in as the merchant
2. Open the Orange Piller extension
3. **Expected:** The arrangement shows status "completed" with repaid amount equal to total debt

### 7. Cannot edit a completed arrangement

1. Log into LNbits as the orange piller
2. Look at the forgiven/completed arrangement row
3. **Expected:** No edit or forgive action buttons are visible (buttons gated on `status === 'active'`)

### 8. Authorization — merchant cannot PUT

1. Using the merchant's API key, send `PUT /orangepiller/api/v1/arrangements/{id}` with `{"reroute_percent": 10}`
2. **Expected:** HTTP 403 Forbidden — only the orange piller who created the arrangement can modify it

## Edge Cases

### Wallet switch refreshes both views

1. Switch between wallets rapidly in the dropdown
2. **Expected:** Both piller arrangements table and merchant section update without errors; no stale data from previous wallet

### Empty merchant arrangements

1. Select a wallet that has no merchant arrangement (e.g., a newly created wallet)
2. **Expected:** No merchant section shown, no error toast, no console errors

### PUT with no update fields

1. Send `PUT /orangepiller/api/v1/arrangements/{id}` with `{}` (empty body) using orange piller's key
2. **Expected:** HTTP 400 with error message about no update fields provided

## Failure Signals

- Merchant section not appearing when logged in as merchant → check `GET /api/v1/merchant/arrangements` response in Network tab
- Edit/forgive buttons visible on completed arrangements → check `v-if` gating in template
- 403 errors when orange piller tries to edit → check wallet key type (must be admin key for PUT)
- Toast errors on wallet switch → check `getMerchantArrangements()` error handling (should silently return [])
- Forgive doesn't change status → check PUT response and `forgiveArrangement()` method

## Requirements Proved By This UAT

- R006 (Merchant transparency view) — Tests 1, 2, 6 prove merchant sees their arrangement details from their own dashboard
- R007 (Arrangement management) — Tests 3, 4, 5, 7, 8 prove orange piller can adjust percentage and forgive debt with proper authorization

## Not Proven By This UAT

- R008 (Clean cutover) — automatic status transition when debt reaches zero via payment (S05)
- R010 (Repayment completion signal) — notification on completion (S05)
- Concurrent management operations — two orange pillers editing simultaneously (unlikely scenario, not tested)

## Notes for Tester

- The test environment may not have `uvloop` installed — this doesn't affect the extension, only the LNbits test runner
- The merchant section appears based on API response, not user role — any wallet that is a `merchant_wallet` in an arrangement will see it
- Edit and forgive buttons use Material Icons (`edit` and `favorite`) — they appear as icon-only buttons in the actions column
- After forgiveness, the arrangement is permanent — there is no undo. The confirmation dialog warns about this.
