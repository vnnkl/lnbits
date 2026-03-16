# S03: Orange piller dashboard — UAT

**Milestone:** M001
**Written:** 2026-03-16

## UAT Type

- UAT mode: mixed (artifact-driven + live-runtime)
- Why this mode is sufficient: Template structure and JS logic can be verified from artifacts, but the full dashboard experience requires a running LNbits instance with the extension loaded and real arrangement data.

## Preconditions

1. LNbits instance running with the orangepiller extension installed
2. At least one user account with the extension enabled (the "orange piller")
3. At least one arrangement created via `POST /orangepiller/api/v1/arrangements` (from S01)
4. Ideally: one active arrangement (repaid_sats < total_debt_sats) and one completed arrangement (repaid_sats == total_debt_sats) to test both status badges

## Smoke Test

Navigate to `/orangepiller` as an authenticated orange piller user → the page loads with a wallet selector and a table showing at least one arrangement row with a progress bar.

## Test Cases

### 1. Dashboard loads with arrangement data

1. Log in to LNbits as the orange piller user
2. Navigate to Extensions → Orange Piller (or directly to `/orangepiller`)
3. Observe the wallet selector at the top of the page
4. **Expected:** The q-table displays arrangement rows with columns: Merchant, Total Debt (sats), Repaid (sats), Remaining (sats), Progress, Reroute %, Status, Created

### 2. Progress bar reflects repayment state

1. Locate an active arrangement where `repaid_sats` < `total_debt_sats`
2. Check the Progress column for that row
3. **Expected:** A colored progress bar is shown. The percentage matches `(repaid_sats / total_debt_sats * 100)` to 2 decimal places. For example, 45000 repaid of 100000 total shows ~45.00%.

### 3. Remaining debt computed correctly

1. For the same arrangement, check the Remaining (sats) column
2. **Expected:** The value equals `total_debt_sats - repaid_sats` exactly. For example, 100000 - 45000 = 55000.

### 4. Status badges distinguish active vs completed

1. Locate an active arrangement (status = "active")
2. Locate a completed arrangement (status = "completed"), or create one by forgiving remaining debt (S04)
3. **Expected:** Active arrangements show an orange chip/badge labeled "active". Completed arrangements show a green chip/badge labeled "completed".

### 5. Wallet selector triggers data refresh

1. If the orange piller has multiple wallets, select a different wallet from the dropdown
2. **Expected:** The table re-fetches arrangement data for the newly selected wallet. The arrangement list updates (may be empty if the second wallet has no arrangements).

### 6. Empty state for wallet with no arrangements

1. Select a wallet that has no associated arrangements
2. **Expected:** The table shows a message like "No arrangements yet" instead of an empty table or error.

### 7. API error handling

1. Open browser DevTools → Network tab
2. Temporarily modify the adminkey (e.g., by editing `localStorage`) to an invalid value, then trigger a wallet change
3. **Expected:** A Quasar toast notification appears indicating an API error. The table does not show stale data from the previous wallet.

## Edge Cases

### Zero repaid (brand new arrangement)

1. Create a new arrangement via the onboarding API (S01)
2. Navigate to the dashboard before any payments are made
3. **Expected:** Progress bar shows 0%, remaining debt equals total debt, status is "active"

### Fully repaid arrangement

1. Have an arrangement where `repaid_sats == total_debt_sats`
2. **Expected:** Progress bar shows 100%, remaining debt is 0, status chip is green "completed"

### Large number of arrangements

1. Create 10+ arrangements for the same wallet
2. **Expected:** All rows render in the q-table. Table pagination or scrolling works correctly.

## Failure Signals

- Page loads but table is empty despite having arrangements → check Network tab for 401 (auth issue) or 500 (server error)
- Progress bar shows NaN or undefined → JS computed field mapping failed, check `total_debt_sats` field name in API response
- No Quasar notification on API error → `LNbits.utils.notifyApiError` not wired correctly
- Wallet selector doesn't trigger refresh → Vue watcher on `selectedWallet` not firing

## Requirements Proved By This UAT

- R005 (Orange piller dashboard) — Proves the orange piller can see all onboarded merchants with payback progress, amounts, percentages, and status

## Not Proven By This UAT

- R006 (Merchant transparency view) — merchant-side dashboard is S04
- R007 (Arrangement management) — adjust/forgive controls are S04
- R010 (Repayment completion signal) — visual status change on completion is S05
- Live payment flow updating the dashboard in real-time (would need S02 + manual payment test)

## Notes for Tester

- The dashboard does not auto-refresh. After making a payment to a merchant, you need to switch wallets and back (or reload the page) to see updated repayment numbers.
- Computed fields (remaining_debt, progress_percent) are calculated in JavaScript, not returned by the API. If they look wrong, compare with raw API response in DevTools Network tab.
- The info sidebar on the right side of the page explains what the extension does — verify it's readable and accurate.
