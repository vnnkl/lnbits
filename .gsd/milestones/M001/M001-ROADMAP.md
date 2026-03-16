# M001: Orange Piller Extension

**Vision:** A standalone LNbits extension that lets Bitcoin enthusiasts onboard local merchants by paying them cash upfront, with automated sat-denominated payback via configurable payment rerouting until the debt is fully repaid.

## Success Criteria

- Orange piller can create a merchant's LNbits account with the extension auto-enabled and a payback arrangement configured, in one flow
- Incoming payments to the merchant are automatically split — configured percentage goes to the orange piller's wallet as an internal transfer
- Debt tracking is exact to the sat, capped on the final payment, and concurrency-safe
- Orange piller sees a dashboard of all onboarded merchants with live payback progress
- Merchant sees arrangement details and repayment progress from their own dashboard
- Orange piller can adjust reroute percentage and forgive remaining debt
- Rerouting stops automatically when debt reaches zero, with visible status change
- Extension installs from a GitHub manifest on any LNbits 1.5.x instance

## Key Risks / Unknowns

- Concurrent payment handling — two payments arriving simultaneously for the same merchant could race on debt tracking, causing overpayment to the orange piller
- Account creation from extension context — the extension must import and call core services (`create_user_account_no_ckeck`), which works for splitpayments-style extensions but hasn't been tested for account creation specifically
- Auto-enable on new account — the extension must be installed on the LNbits instance before it can be listed in `default_exts` for a new user

## Proof Strategy

- Concurrent payments → retire in S02 by proving two rapid-fire payments to the same merchant result in correct debt tracking (no overpayment)
- Account creation from extension → retire in S01 by proving the onboarding API successfully creates an account, wallet, and arrangement in one call
- Auto-enable → retire in S01 by proving the new merchant account has the orangepiller extension active immediately

## Verification Classes

- Contract verification: Python tests, API response checks, migration verification
- Integration verification: End-to-end payment flow — pay merchant wallet, verify split arrives in orange piller wallet, verify debt decremented
- Operational verification: Extension installs from GitHub, survives LNbits restart
- UAT / human verification: Onboarding UX flow, dashboard readability

## Milestone Definition of Done

This milestone is complete only when all are true:

- All 5 slices are complete with passing verification
- The full end-to-end flow works: onboard → pay → reroute → track → complete
- Both orange piller and merchant dashboards show accurate arrangement state
- Arrangement management (adjust %, forgive) works correctly
- Clean cutover is proven: debt hits zero, rerouting stops, status updates
- Extension installs from GitHub manifest on a clean LNbits instance
- Success criteria are verified against a running LNbits instance, not just unit tests

## Requirement Coverage

- Covers: R001, R002, R003, R004, R005, R006, R007, R008, R009, R010
- Partially covers: none
- Leaves for later: R011 (store map listing)
- Orphan risks: none

## Slices

- [ ] **S01: Extension scaffold + onboarding API** `risk:high` `depends:[]`
  > After this: Orange piller fills a form in the extension UI → merchant LNbits account created with extension auto-enabled, payback arrangement stored in DB. Verified via API and DB state.

- [ ] **S02: Payment rerouting engine** `risk:high` `depends:[S01]`
  > After this: Pay the merchant's wallet → configured percentage arrives in orange piller's wallet as internal transfer, debt decremented. Exact cap on final payment. Concurrency-safe. Verified by making real payments on a running LNbits instance.

- [ ] **S03: Orange piller dashboard** `risk:low` `depends:[S01,S02]`
  > After this: Orange piller opens the extension and sees all onboarded merchants with payback progress bars, amounts, percentages, and arrangement status.

- [ ] **S04: Merchant view + arrangement management** `risk:low` `depends:[S01,S02]`
  > After this: Merchant sees their payback arrangement details from their own LNbits. Orange piller can adjust reroute percentage and forgive remaining debt from the dashboard.

- [ ] **S05: Clean cutover, notifications & packaging** `risk:low` `depends:[S02,S03,S04]`
  > After this: Debt reaches zero → rerouting stops automatically, status changes to "completed" on both dashboards. Extension repo has config.json + manifest.json and is installable from GitHub.

## Boundary Map

### S01 → S02

Produces:
- `models.py` → `Arrangement` model (id, orange_piller_wallet, merchant_wallet, merchant_user_id, total_debt_sats, repaid_sats, reroute_percent, status, created_at)
- `crud.py` → `get_arrangement_by_merchant_wallet(wallet_id)` for looking up active arrangements when payments arrive
- `crud.py` → `update_arrangement_repaid(arrangement_id, additional_sats)` for atomic debt updates
- `migrations.py` → `orangepiller.arrangements` table
- DB schema → `arrangements` table with the fields above

Consumes:
- nothing (first slice)

### S01 → S03

Produces:
- `crud.py` → `get_arrangements_by_piller(wallet_id)` returning all arrangements for an orange piller
- `models.py` → `Arrangement` model with computed properties (remaining_debt, progress_percent, is_completed)
- `views_api.py` → `GET /api/v1/arrangements` returning arrangement list for authenticated user

Consumes:
- nothing (first slice)

### S01 → S04

Produces:
- `crud.py` → `get_arrangement_by_merchant_wallet(wallet_id)` for merchant's own view
- `crud.py` → `update_arrangement(arrangement_id, ...)` for percent adjustment and forgiveness
- `views_api.py` → `PUT /api/v1/arrangements/{id}` for arrangement updates

Consumes:
- nothing (first slice)

### S02 → S05

Produces:
- `tasks.py` → payment listener that checks arrangement status before rerouting (skips completed arrangements)
- `crud.py` → atomic `update_arrangement_repaid` that transitions status to "completed" when debt reaches zero

Consumes from S01:
- `crud.py` → `get_arrangement_by_merchant_wallet` to look up active arrangements
- `crud.py` → `update_arrangement_repaid` for debt tracking
- `models.py` → `Arrangement` model

### S03 → S05

Produces:
- `templates/orangepiller/index.html` → dashboard template with arrangement cards showing status

Consumes from S01:
- `views_api.py` → `GET /api/v1/arrangements`
- `models.py` → `Arrangement` model

### S04 → S05

Produces:
- Merchant view template showing arrangement status
- `views_api.py` → `PUT /api/v1/arrangements/{id}` for forgiveness

Consumes from S01:
- `crud.py` → `get_arrangement_by_merchant_wallet`, `update_arrangement`
- `models.py` → `Arrangement` model
