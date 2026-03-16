# Requirements

This file is the explicit capability and coverage contract for the Orange Piller extension.

## Active

### R104 — TPoS link and QR on dashboards
- Class: primary-user-loop
- Status: active
- Description: Both orange piller and merchant dashboards display the TPoS shareable URL as a clickable link and a QR code. The link opens the TPoS payment page directly.
- Why it matters: The orange piller needs to share the payment link with the merchant; the merchant needs quick access to their own payment terminal.
- Source: user
- Primary owning slice: M002/S02
- Supporting slices: none
- Validation: unmapped
- Notes: QR code generated client-side using a JS library already available in LNbits (or a lightweight one). Only shown when tpos_url is present.

### R105 — Printable merchant poster with QR code
- Class: primary-user-loop
- Status: active
- Description: A dedicated route serves a printable HTML page with the merchant's business name, "Pay with Bitcoin" branding, and a QR code pointing to the TPoS payment page. Designed for printing and placing at the merchant's counter.
- Why it matters: The orange piller walks out of the shop with something physical to hand the merchant — a poster that makes Bitcoin payments possible without any merchant training.
- Source: user
- Primary owning slice: M002/S02
- Supporting slices: none
- Validation: unmapped
- Notes: Standalone page, no LNbits chrome. Print-optimized CSS. Accessible via a link from the dashboard.

## Validated

### R001 — Merchant onboarding
- Class: core-capability
- Status: validated
- Description: Orange piller can create a full LNbits account + wallet for a merchant, with the Orange Piller extension auto-enabled from the start.
- Why it matters: This is the entry point to the entire flow — without account creation, nothing else works.
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: none
- Validation: POST endpoint atomically creates merchant account + wallet + arrangement; create_user_account_no_ckeck called with default_exts; import tests and route inspection pass; 20/20 tests pass
- Notes: Uses `create_user_account_no_ckeck` with `default_exts=["orangepiller"]`. Must create the payback arrangement atomically with the account.

### R002 — Payback arrangement configuration
- Class: core-capability
- Status: validated
- Description: Orange piller can set a sat-denominated debt amount and a reroute percentage (1-100%) per merchant arrangement.
- Why it matters: This defines the economic relationship between orange piller and merchant.
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: M001/S04
- Validation: CreateArrangement model validates debt/percent; PUT endpoint allows post-creation percent adjustment; 6 merchant API tests pass
- Notes: Debt tracked in sats. Percentage determines what fraction of each incoming payment is rerouted. Orange piller can adjust percentage and forgive debt after creation.

### R003 — Payment rerouting engine
- Class: core-capability
- Status: validated
- Description: Incoming payments to the merchant's wallet are automatically split — the configured percentage is internally transferred to the orange piller's wallet. Must be concurrency-safe (two simultaneous payments must not cause overpayment beyond the debt ceiling).
- Why it matters: This is the core mechanic that makes the whole extension work.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: on_invoice_paid intercepts payments with tag guard, calculates split, performs internal transfer; atomic SQL prevents concurrent overpayment; 11 reroute tests pass
- Notes: Uses `register_invoice_listener` pattern from splitpayments. Internal transfers only (same LNbits instance). Must handle edge case where reroute amount exceeds remaining debt — cap at remaining.

### R004 — Exact debt tracking with final payment cap
- Class: core-capability
- Status: validated
- Description: The orange piller receives exactly the owed sat amount — not a sat more. On the final payment that would complete the debt, only the remaining amount is rerouted.
- Why it matters: Fairness to the merchant. The arrangement is precise.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: min(reroute_amount, remaining_debt) enforced in Python; SQL CASE caps repaid_sats at total_debt_sats; test_cap_at_remaining_debt and test_exact_payoff pass
- Notes: `min(reroute_amount, remaining_debt)` on every payment.

### R005 — Orange piller dashboard
- Class: primary-user-loop
- Status: validated
- Description: Orange piller sees all merchants they've onboarded — each with payback progress (amount repaid / total debt), reroute percentage, and arrangement status.
- Why it matters: The orange piller needs visibility into their portfolio of onboarded merchants.
- Source: user
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: Quasar dashboard with q-table, q-linear-progress bars, status chips; computed fields verified (remaining_debt=55000, progress_percent=45.00)
- Notes: Multi-merchant support from the start.

### R006 — Merchant transparency view
- Class: primary-user-loop
- Status: validated
- Description: Merchant can see the payback arrangement details from their own LNbits dashboard — how much was fronted, how much has been repaid, what percentage is being rerouted, and when it will end.
- Why it matters: Full transparency builds trust between orange piller and merchant.
- Source: user
- Primary owning slice: M001/S04
- Supporting slices: none
- Validation: Merchant GET endpoint at /api/v1/merchant/arrangements; conditional section in dashboard template; 6 merchant API tests pass
- Notes: Merchant sees their own view of the arrangement, not the orange piller's full dashboard.

### R007 — Arrangement management
- Class: core-capability
- Status: validated
- Description: Orange piller can adjust the reroute percentage and forgive remaining debt (releasing the merchant) on any active arrangement.
- Why it matters: Flexibility — circumstances change, and the orange piller should have control.
- Source: user
- Primary owning slice: M001/S04
- Supporting slices: none
- Validation: PUT /api/v1/arrangements/{id} with auth check; edit dialog (1-100 validation) and forgive dialog with confirmation; 6 merchant API tests cover all paths
- Notes: No merchant-side dispute mechanism — merchant accepted cash upfront.

### R008 — Clean cutover
- Class: core-capability
- Status: validated
- Description: When the debt reaches zero, rerouting stops automatically. The merchant's LNbits works normally with no payment interception.
- Why it matters: The arrangement has a clear end — the merchant isn't locked into perpetual splits.
- Source: user
- Primary owning slice: M001/S05
- Supporting slices: M001/S02
- Validation: 3 cutover tests prove debt-zero → completed → skip path (test_cutover.py)
- Notes: Arrangement status transitions from "active" to "completed". The extension remains installed but becomes transparent.

### R009 — Standalone extension packaging
- Class: launchability
- Status: validated
- Description: Extension is a standalone GitHub repo with config.json, manifest.json, installable via LNbits extension manager.
- Why it matters: Must be distributable as a standard LNbits extension — not a core patch.
- Source: user
- Primary owning slice: M001/S05
- Supporting slices: M001/S01
- Validation: config.json validates with all required fields; tile/README/LICENSE/description.md present. Install-from-GitHub deferred to UAT.
- Notes: Follow splitpayments/example extension repo structure exactly.

### R010 — Repayment completion signal
- Class: failure-visibility
- Status: validated
- Description: When debt is fully repaid, both orange piller and merchant see a visual status change. Notification if easy to implement.
- Why it matters: Both parties need to know the arrangement is done.
- Source: user
- Primary owning slice: M001/S05
- Supporting slices: none
- Validation: Toast notification code present in JS with transition-aware detection; status chips show completion state. Visual verification deferred to UAT.
- Notes: At minimum a status change on both dashboards. Push notification or in-app notification as stretch.

### R101 — TPoS auto-provisioning during onboarding
- Class: core-capability
- Status: validated
- Description: When the orange piller creates an arrangement, a TPoS terminal is automatically created on the merchant's wallet via the TPoS extension API. The TPoS ID and shareable URL are stored on the arrangement.
- Why it matters: Without a payment terminal, the merchant has no way to accept Bitcoin at their counter — the rerouting engine sits idle.
- Source: user
- Primary owning slice: M002/S01
- Supporting slices: none
- Validation: POST handler calls httpx POST to /tpos/api/v1/tposs with merchant adminkey; tpos_id and tpos_url stored on arrangement; proven by test_create_arrangement_with_tpos and test_httpx_called_with_tpos_payload; 29/29 tests pass
- Notes: Uses internal HTTP call to TPoS API (`POST /tpos/api/v1/tposs`) with the merchant wallet's adminkey. TPoS added to `default_exts` during account creation only when detected as installed.

### R102 — Extended onboarding form with merchant/TPoS settings
- Class: primary-user-loop
- Status: validated
- Description: The onboarding form includes core TPoS configuration fields: merchant name, currency, tip options, tax default, tax inclusive toggle, and business info (name, address, VAT ID).
- Why it matters: The orange piller needs to configure the merchant's payment terminal during onboarding — they can't do it later without the merchant's login.
- Source: user
- Primary owning slice: M002/S01
- Supporting slices: M002/S02
- Validation: CreateArrangement model accepts all 8 fields with correct defaults; test_extended_create_fields_accepted and test_extended_create_fields_defaults pass; fields passed through to TPoS payload via httpx
- Notes: Power-user TPoS features (inventory, ATM/withdraw, Stripe, remote mode) are omitted — merchant can configure those later from their own TPoS admin.

### R103 — Graceful degradation when TPoS not installed
- Class: failure-visibility
- Status: validated
- Description: If TPoS is not installed on the LNbits instance, onboarding still succeeds — the arrangement is created without a TPoS terminal. The orange piller sees a warning that no payment terminal was provisioned.
- Why it matters: The extension shouldn't break if the LNbits admin hasn't installed TPoS.
- Source: user
- Primary owning slice: M002/S01
- Supporting slices: none
- Validation: test_create_arrangement_without_tpos proves tpos_id=None and warning present; test_default_exts_omits_tpos_when_not_installed proves "tpos" excluded from default_exts; test_create_arrangement_tpos_http_failure proves httpx failure handled gracefully
- Notes: TPoS URL fields on the arrangement will be null/empty. Dashboards should display an informative message instead of a broken link.

### R106 — Merchant login credentials surfaced to orange piller
- Class: primary-user-loop
- Status: validated
- Description: After onboarding, the orange piller receives the merchant's LNbits login URL so they can share access to the merchant's full LNbits dashboard.
- Why it matters: The merchant needs a way to access their own LNbits account to see their arrangement, configure settings, and eventually manage their wallet independently.
- Source: inferred
- Primary owning slice: M002/S01
- Supporting slices: M002/S02
- Validation: merchant_credentials contains /wallet?usr={user_id} login URL; proven by test_merchant_credentials_format_with_tpos and test_merchant_credentials_format_without_tpos — always populated regardless of TPoS status
- Notes: Uses LNbits standard user-id auth pattern. `create_user_account_no_ckeck` returns User object with `.id` used to construct the login URL.

## Deferred

### R011 — Bitcoin store map listing
- Class: differentiator
- Status: deferred
- Description: Merchants onboarded via Orange Piller are automatically listed on a Bitcoin-accepting store map.
- Why it matters: Drives customers to the merchant, creating a flywheel for Bitcoin adoption.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: User explicitly said not needed in first version. Would likely be a separate extension or integration.

## Out of Scope

### R012 — Fiat-denominated debt tracking
- Class: constraint
- Status: out-of-scope
- Description: Tracking the payback debt in fiat (EUR) with exchange rate conversion on each payment.
- Why it matters: Prevents scope confusion — debt is tracked in sats, period.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: User chose sats-denominated tracking. No exchange rate dependencies.

### R013 — External Lightning destination for payback
- Class: constraint
- Status: out-of-scope
- Description: Allowing the orange piller to receive payback at an external Lightning address or LNURL instead of a local LNbits wallet.
- Why it matters: Keeps rerouting simple — internal transfers are instant, free, and can't fail due to routing.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: User chose same-instance only. Could be revisited later.

### R014 — Merchant dispute mechanism
- Class: anti-feature
- Status: out-of-scope
- Description: Allowing the merchant to dispute or request changes to the payback arrangement.
- Why it matters: The merchant accepted cash upfront — there is nothing to dispute.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: User explicitly ruled this out.

### R015 — Full TPoS configuration during onboarding
- Class: constraint
- Status: out-of-scope
- Description: Exposing all ~20 TPoS settings (inventory, ATM/withdraw, Stripe, receipt printing, remote mode) in the onboarding form.
- Why it matters: Prevents scope creep — power-user TPoS features are accessible via the merchant's own TPoS admin later.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Core settings (name, currency, tips, tax, business info) are in scope. Advanced features deferred to merchant self-service.

## Traceability

| ID | Class | Status | Primary owner | Supporting | Proof |
|---|---|---|---|---|---|
| R001 | core-capability | validated | M001/S01 | none | POST endpoint + import tests |
| R002 | core-capability | validated | M001/S01 | M001/S04 | model validation + PUT tests |
| R003 | core-capability | validated | M001/S02 | none | 11 reroute tests |
| R004 | core-capability | validated | M001/S02 | none | cap + exact payoff tests |
| R005 | primary-user-loop | validated | M001/S03 | none | dashboard template + computed field check |
| R006 | primary-user-loop | validated | M001/S04 | none | merchant GET + template |
| R007 | core-capability | validated | M001/S04 | none | PUT auth + 6 merchant tests |
| R008 | core-capability | validated | M001/S05 | M001/S02 | test_cutover.py |
| R009 | launchability | validated | M001/S05 | M001/S01 | config.json + artifacts |
| R010 | failure-visibility | validated | M001/S05 | none | toast notification code |
| R101 | core-capability | validated | M002/S01 | none | httpx POST to TPoS API + 2 tests |
| R102 | primary-user-loop | validated | M002/S01 | M002/S02 | CreateArrangement 8 fields + 2 tests |
| R103 | failure-visibility | validated | M002/S01 | none | 3 degradation tests |
| R104 | primary-user-loop | active | M002/S02 | none | unmapped |
| R105 | primary-user-loop | active | M002/S02 | none | unmapped |
| R106 | primary-user-loop | validated | M002/S01 | M002/S02 | merchant_credentials URL + 2 tests |
| R011 | differentiator | deferred | none | none | unmapped |
| R012 | constraint | out-of-scope | none | none | n/a |
| R013 | constraint | out-of-scope | none | none | n/a |
| R014 | anti-feature | out-of-scope | none | none | n/a |
| R015 | constraint | out-of-scope | none | none | n/a |

## Coverage Summary

- Active requirements: 2
- Mapped to slices: 2
- Validated: 14
- Unmapped active requirements: 0
