# S05: Clean cutover, notifications & packaging — UAT

**Milestone:** M001
**Written:** 2026-03-16

## UAT Type

- UAT mode: mixed (artifact-driven for packaging, live-runtime for cutover and notifications)
- Why this mode is sufficient: Packaging can be verified by file inspection; cutover and notifications require a running LNbits instance with real payment flows

## Preconditions

- LNbits instance running (1.3.0+) with the orangepiller extension installed from the repo
- At least one orange piller account with an active arrangement (merchant with non-zero remaining debt)
- Orange piller has a funded wallet (enough sats to create test payments to the merchant)
- Browser open to the LNbits UI, logged in as the orange piller

## Smoke Test

1. Navigate to the Extensions page in LNbits
2. Verify Orange Piller appears with an orange tile image, name, and description
3. Click into the extension — dashboard loads with at least one arrangement visible

## Test Cases

### 1. Extension packaging validates in extension manager

1. Open the LNbits Extensions / Manage page
2. Verify Orange Piller extension appears with tile image (orange square), name, and short description
3. Click the extension to view details
4. **Expected:** Extension info shows version 0.1.0, MIT license, description text. No validation errors or broken images.

### 2. Clean cutover — debt reaches zero, rerouting stops

1. Create a new arrangement: orange piller wallet → merchant wallet, total_debt_sats = 1000, reroute_percent = 100
2. From an external wallet, pay the merchant's wallet exactly 1000 sats
3. Check the orange piller's wallet balance — should have received 1000 sats
4. Check the arrangement status on the orange piller dashboard
5. **Expected:** Arrangement status shows "Completed" (green chip). Repaid shows 1000/1000 sats. Progress bar at 100%.

### 3. Completed arrangement — subsequent payments not rerouted

1. Using the completed arrangement from Test 2, send another 500 sats to the merchant's wallet
2. Check the orange piller's wallet balance
3. Check the merchant's wallet balance
4. **Expected:** Orange piller balance unchanged (no reroute). Merchant receives the full 500 sats. Arrangement still shows "Completed".

### 4. Toast notification on completion transition

1. Create a new arrangement: total_debt_sats = 500, reroute_percent = 100
2. Open the orange piller dashboard in one browser tab
3. Send 500 sats to the merchant's wallet from an external wallet
4. Wait for the dashboard to refresh (auto-poll or manual refresh)
5. **Expected:** A green Quasar toast notification appears saying the arrangement with this merchant is now completed. The arrangement card shows "Completed" status.

### 5. Merchant sees completion on their dashboard

1. Log in as the merchant whose arrangement just completed (from Test 4)
2. Navigate to the Orange Piller extension
3. **Expected:** Merchant view shows the arrangement as "Completed" with full repayment progress. If merchant had the page open during completion, a toast notification appeared.

### 6. Exact payoff cap — partial final payment

1. Create a new arrangement: total_debt_sats = 1000, reroute_percent = 50
2. Send 1500 sats to the merchant — reroute amount would be 750 sats (50% of 1500)
3. Check: orange piller received 750, merchant kept 750, remaining debt = 250
4. Send another 1000 sats — reroute would be 500, but only 250 remaining
5. **Expected:** Orange piller receives exactly 250 sats (capped at remaining debt). Merchant keeps 750 sats. Arrangement status = "Completed". Total repaid = 1000/1000.

### 7. config.json field validation

1. Run: `python3 -c "import json; c=json.load(open('orangepiller/config.json')); print(c['version'], c['license'], c['min_lnbits_version'])"`
2. **Expected:** Output: `0.1.0 MIT 1.3.0`

### 8. Documentation files present

1. Run: `ls orangepiller/README.md orangepiller/LICENSE orangepiller/description.md orangepiller/static/image/orange-piller.png`
2. Open README.md — verify it has install instructions and usage overview
3. Open LICENSE — verify it's MIT license
4. **Expected:** All files exist. README has meaningful content. LICENSE is MIT.

## Edge Cases

### Race condition — two payments completing debt simultaneously

1. Create arrangement with total_debt_sats = 1000, reroute_percent = 100, repaid_sats already at 900
2. Send two 200-sat payments to the merchant within <1 second
3. **Expected:** Orange piller receives exactly 100 sats total (not 200). One payment reroutes 100 and completes; the other is skipped. Arrangement status = "Completed".

### Forgiven arrangement — no rerouting

1. Create arrangement, then forgive the remaining debt via the management UI
2. Send a payment to the merchant
3. **Expected:** No rerouting occurs. Status shows "Completed" (forgiven). Merchant receives full payment.

### Zero-debt arrangement at creation

1. Try to create an arrangement with total_debt_sats = 0
2. **Expected:** Either rejected by validation or immediately marked as "completed" — no rerouting should ever occur.

## Failure Signals

- Broken/missing tile image in extension manager → `orange-piller.png` missing or path wrong in config.json
- Extension won't install → config.json missing required fields or malformed
- No toast notification on completion → JS error in `_detectCompletionTransitions`; check browser console
- Overpayment to orange piller → atomic debt update not capping correctly; check `update_arrangement_repaid` SQL
- Rerouting continues after completion → `on_invoice_paid` not checking arrangement status before transfer

## Requirements Proved By This UAT

- R008 (Clean cutover) — Tests 2, 3, 6 prove rerouting stops at debt zero with exact cap
- R009 (Standalone extension packaging) — Tests 1, 7, 8 prove extension is installable with all metadata
- R010 (Repayment completion signal) — Tests 4, 5 prove visible notification on both dashboards

## Not Proven By This UAT

- R009 install-from-GitHub specifically — requires publishing to a GitHub repo and installing via URL in extension manager (operational verification)
- Performance under high concurrency beyond 2 simultaneous payments
- LNbits restart resilience — extension survives restart with arrangements intact

## Notes for Tester

- The tile image is a solid orange placeholder square — this is intentional for now. Replace with branded artwork before public release.
- Toast notifications only fire on *transitions*, not on page load. You must have the dashboard open before the completing payment arrives to see the toast.
- The `images` array in config.json is empty — the extension manager gallery won't show screenshots. This is expected.
- Tests in `test_cutover.py` use mocks and don't require a running LNbits instance. The UAT cases above are the live-runtime verification.
