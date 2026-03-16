# Requirements

This file is the explicit capability and coverage contract for the Orange Piller extension.

## Active

### R101 — TPoS auto-provisioning during onboarding
- Class: core-capability
- Status: active
- Description: When the orange piller creates an arrangement, a TPoS terminal is automatically created on the merchant's wallet via the TPoS extension API. The TPoS ID and shareable URL are stored on the arrangement.
- Why it matters: Without a payment terminal, the merchant has no way to accept Bitcoin at their counter — the rerouting engine sits idle.
- Source: user
- Primary owning slice: M002/S01
- Supporting slices: none
- Validation: unmapped
- Notes: Uses internal HTTP call to TPoS API (`POST /tpos/api/v1/tposs`) with the merchant wallet's adminkey. TPoS must also be added to `default_exts` during account creation so it's enabled on the merchant's account.

### R102 — Extended onboarding form with merchant/TPoS settings
- Class: primary-user-loop
- Status: active
- Description: The onboarding form includes core TPoS configuration fields: merchant name, currency, tip options, tax default, tax inclusive toggle, and business info (name, address, VAT ID).
- Why it matters: The orange piller needs to configure the merchant's payment terminal during onboarding — they can't do it later without the merchant's login.
- Source: user
- Primary owning slice: M002/S01
- Supporting slices: M002/S02
- Validation: unmapped
- Notes: Power-user TPoS features (inventory, ATM/withdraw, Stripe, remote mode) are omitted — merchant can configure those later from their own TPoS admin.

### R103 — Graceful degradation when TPoS not installed
- Class: failure-visibility
- Status: active
- Description: If TPoS is not installed on the LNbits instance, onboarding still succeeds — the arrangement is created without a TPoS terminal. The orange piller sees a warning that no payment terminal was provisioned.
- Why it matters: The extension shouldn't break if the LNbits admin hasn't installed TPoS.
- Source: user
- Primary owning slice: M002/S01
- Supporting slices: none
- Validation: unmapped
- Notes: TPoS URL fields on the arrangement will be null/empty. Dashboards should display an informative message instead of a broken link.

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

### R106 — Merchant login credentials surfaced to orange piller
- Class: primary-user-loop
- Status: active
- Description: After onboarding, the orange piller receives the merchant's LNbits login URL (or credentials) so they can share access to the merchant's full LNbits dashboard.
- Why it matters: The merchant needs a way to access their own LNbits account to see their arrangement, configure settings, and eventually manage their wallet independently.
- Source: inferred
- Primary owning slice: M002/S01
- Supporting slices: M002/S02
- Validation: unmapped
- Notes: Need to determine what `create_user_account_no_ckeck` returns for authentication — may be a username/password, an auth token, or a direct login link. Surface whatever is available.

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
| R101 | core-capability | active | M002/S01 | none | unmapped |
| R102 | primary-user-loop | active | M002/S01 | M002/S02 | unmapped |
| R103 | failure-visibility | active | M002/S01 | none | unmapped |
| R104 | primary-user-loop | active | M002/S02 | none | unmapped |
| R105 | primary-user-loop | active | M002/S02 | none | unmapped |
| R106 | primary-user-loop | active | M002/S01 | M002/S02 | unmapped |
| R011 | differentiator | deferred | none | none | unmapped |
| R012 | constraint | out-of-scope | none | none | n/a |
| R013 | constraint | out-of-scope | none | none | n/a |
| R014 | anti-feature | out-of-scope | none | none | n/a |
| R015 | constraint | out-of-scope | none | none | n/a |

## Coverage Summary

- Active requirements: 6
- Mapped to slices: 6
- Validated: 10
- Unmapped active requirements: 0
