# Requirements

This file is the explicit capability and coverage contract for the Orange Piller extension.

## Active

### R001 — Merchant onboarding
- Class: core-capability
- Status: active
- Description: Orange piller can create a full LNbits account + wallet for a merchant, with the Orange Piller extension auto-enabled from the start.
- Why it matters: This is the entry point to the entire flow — without account creation, nothing else works.
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: none
- Validation: unmapped
- Notes: Uses `create_user_account_no_ckeck` with `default_exts=["orangepiller"]`. Must create the payback arrangement atomically with the account.

### R002 — Payback arrangement configuration
- Class: core-capability
- Status: active
- Description: Orange piller can set a sat-denominated debt amount and a reroute percentage (1-100%) per merchant arrangement.
- Why it matters: This defines the economic relationship between orange piller and merchant.
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: M001/S04
- Validation: unmapped
- Notes: Debt tracked in sats. Percentage determines what fraction of each incoming payment is rerouted. Orange piller can adjust percentage and forgive debt after creation.

### R003 — Payment rerouting engine
- Class: core-capability
- Status: active
- Description: Incoming payments to the merchant's wallet are automatically split — the configured percentage is internally transferred to the orange piller's wallet. Must be concurrency-safe (two simultaneous payments must not cause overpayment beyond the debt ceiling).
- Why it matters: This is the core mechanic that makes the whole extension work.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: unmapped
- Notes: Uses `register_invoice_listener` pattern from splitpayments. Internal transfers only (same LNbits instance). Must handle edge case where reroute amount exceeds remaining debt — cap at remaining.

### R004 — Exact debt tracking with final payment cap
- Class: core-capability
- Status: active
- Description: The orange piller receives exactly the owed sat amount — not a sat more. On the final payment that would complete the debt, only the remaining amount is rerouted.
- Why it matters: Fairness to the merchant. The arrangement is precise.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: unmapped
- Notes: `min(reroute_amount, remaining_debt)` on every payment.

### R005 — Orange piller dashboard
- Class: primary-user-loop
- Status: active
- Description: Orange piller sees all merchants they've onboarded — each with payback progress (amount repaid / total debt), reroute percentage, and arrangement status.
- Why it matters: The orange piller needs visibility into their portfolio of onboarded merchants.
- Source: user
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: unmapped
- Notes: Multi-merchant support from the start.

### R006 — Merchant transparency view
- Class: primary-user-loop
- Status: active
- Description: Merchant can see the payback arrangement details from their own LNbits dashboard — how much was fronted, how much has been repaid, what percentage is being rerouted, and when it will end.
- Why it matters: Full transparency builds trust between orange piller and merchant.
- Source: user
- Primary owning slice: M001/S04
- Supporting slices: none
- Validation: unmapped
- Notes: Merchant sees their own view of the arrangement, not the orange piller's full dashboard.

### R007 — Arrangement management
- Class: core-capability
- Status: active
- Description: Orange piller can adjust the reroute percentage and forgive remaining debt (releasing the merchant) on any active arrangement.
- Why it matters: Flexibility — circumstances change, and the orange piller should have control.
- Source: user
- Primary owning slice: M001/S04
- Supporting slices: none
- Validation: unmapped
- Notes: No merchant-side dispute mechanism — merchant accepted cash upfront.

### R008 — Clean cutover
- Class: core-capability
- Status: active
- Description: When the debt reaches zero, rerouting stops automatically. The merchant's LNbits works normally with no payment interception.
- Why it matters: The arrangement has a clear end — the merchant isn't locked into perpetual splits.
- Source: user
- Primary owning slice: M001/S05
- Supporting slices: M001/S02
- Validation: unmapped
- Notes: Arrangement status transitions from "active" to "completed". The extension remains installed but becomes transparent.

### R009 — Standalone extension packaging
- Class: launchability
- Status: active
- Description: Extension is a standalone GitHub repo with config.json, manifest.json, installable via LNbits extension manager.
- Why it matters: Must be distributable as a standard LNbits extension — not a core patch.
- Source: user
- Primary owning slice: M001/S05
- Supporting slices: M001/S01
- Validation: unmapped
- Notes: Follow splitpayments/example extension repo structure exactly.

### R010 — Repayment completion signal
- Class: failure-visibility
- Status: active
- Description: When debt is fully repaid, both orange piller and merchant see a visual status change. Notification if easy to implement.
- Why it matters: Both parties need to know the arrangement is done.
- Source: user
- Primary owning slice: M001/S05
- Supporting slices: none
- Validation: unmapped
- Notes: At minimum a status change on both dashboards. Push notification or in-app notification as stretch.

## Validated

(none yet)

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

## Traceability

| ID | Class | Status | Primary owner | Supporting | Proof |
|---|---|---|---|---|---|
| R001 | core-capability | active | M001/S01 | none | unmapped |
| R002 | core-capability | active | M001/S01 | M001/S04 | unmapped |
| R003 | core-capability | active | M001/S02 | none | unmapped |
| R004 | core-capability | active | M001/S02 | none | unmapped |
| R005 | primary-user-loop | active | M001/S03 | none | unmapped |
| R006 | primary-user-loop | active | M001/S04 | none | unmapped |
| R007 | core-capability | active | M001/S04 | none | unmapped |
| R008 | core-capability | active | M001/S05 | M001/S02 | unmapped |
| R009 | launchability | active | M001/S05 | M001/S01 | unmapped |
| R010 | failure-visibility | active | M001/S05 | none | unmapped |
| R011 | differentiator | deferred | none | none | unmapped |
| R012 | constraint | out-of-scope | none | none | n/a |
| R013 | constraint | out-of-scope | none | none | n/a |
| R014 | anti-feature | out-of-scope | none | none | n/a |

## Coverage Summary

- Active requirements: 10
- Mapped to slices: 10
- Validated: 0
- Unmapped active requirements: 0
