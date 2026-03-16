# S04: Merchant view + arrangement management

**Goal:** Merchant sees their payback arrangement details from their own LNbits. Orange piller can adjust reroute percentage and forgive remaining debt from the dashboard.
**Demo:** Merchant logs into LNbits → opens Orange Piller extension → sees their arrangement with progress. Orange piller clicks edit on an arrangement → changes reroute % → saves. Orange piller clicks forgive → confirms → arrangement status changes to completed.

## Must-Haves

- Merchant GET endpoint returns arrangements where authenticated wallet is the merchant_wallet
- PUT endpoint accepts reroute_percent updates (1–100) on active arrangements only
- PUT endpoint accepts forgiveness (sets repaid_sats = total_debt_sats, status = "completed")
- Authorization: only the orange piller who created the arrangement can PUT
- Merchant view section in index.html shows arrangement details conditionally
- Orange piller table has action buttons for edit and forgive
- Edit dialog for reroute_percent with validation
- Forgive action has confirmation dialog

## Proof Level

- This slice proves: contract + UI integration
- Real runtime required: no (contract tests + code inspection)
- Human/UAT required: yes (dashboard UX — deferred to S05 integration)

## Verification

- `pytest tests/extensions/orangepiller/test_merchant_api.py -v` — all tests pass
- Code inspection: PUT endpoint checks `key_info.wallet.id == arrangement.orange_piller_wallet`
- Code inspection: merchant GET filters by `merchant_wallet`, not `orange_piller_wallet`
- Code inspection: index.html has conditional merchant section and management controls
- Code inspection: index.js has `getMerchantArrangements()`, `updateArrangement()`, `forgiveArrangement()` methods

## Observability / Diagnostics

- Runtime signals: loguru INFO on arrangement update (percent change or forgiveness) with arrangement_id and action type
- Inspection surfaces: `GET /api/v1/merchant/arrangements` for merchant view; `GET /api/v1/arrangements` for orange piller view
- Failure visibility: HTTP 403 for unauthorized PUT attempts, HTTP 400 for invalid updates (completed arrangement, bad percent)

## Integration Closure

- Upstream surfaces consumed: `crud.py` → `get_arrangement_by_merchant_wallet`, `update_arrangement`, `get_arrangement`; `models.py` → `Arrangement`; S03's `index.html` template and `index.js`
- New wiring introduced: merchant GET endpoint, real PUT endpoint, UpdateArrangement model, merchant UI section, management controls
- What remains before the milestone is truly usable end-to-end: S05 (clean cutover notifications, packaging)

## Tasks

- [x] **T01: Implement merchant GET and arrangement PUT endpoints** `est:30m`
  - Why: Backend must exist before frontend can wire to it. Delivers R006 (merchant API) and R007 (management API).
  - Files: `orangepiller/views_api.py`, `orangepiller/models.py`, `tests/extensions/orangepiller/test_merchant_api.py`
  - Do: Add `UpdateArrangement` model (optional `reroute_percent`, optional `forgive` bool). Add `GET /api/v1/merchant/arrangements` that returns arrangements where `merchant_wallet == key_info.wallet.id`. Replace PUT stub with real handler: fetch arrangement, check auth (`orange_piller_wallet == wallet.id`), reject updates on completed arrangements, handle forgiveness (`repaid_sats=total_debt_sats, status="completed"`), handle percent update. Add loguru logging. Write unit tests covering: merchant GET returns correct data, PUT auth rejection, PUT on completed arrangement, PUT forgiveness, PUT percent update, PUT validation.
  - Verify: `pytest tests/extensions/orangepiller/test_merchant_api.py -v` passes
  - Done when: Both endpoints work with correct auth, validation, and all tests pass

- [x] **T02: Add merchant view section and management controls to dashboard** `est:45m`
  - Why: Delivers the user-facing UI for R006 (merchant sees arrangement) and R007 (orange piller manages arrangements).
  - Files: `orangepiller/templates/orangepiller/index.html`, `orangepiller/static/js/index.js`
  - Do: In index.js: add `merchantArrangements` data array, `getMerchantArrangements()` method calling merchant endpoint, `updateArrangement(id, data)` and `forgiveArrangement(id)` methods, edit dialog state (`showEditDialog`, `editForm`). Watch `selectedWallet` to also call `getMerchantArrangements()`. In index.html: add merchant section (conditionally shown via `v-if="merchantArrangements.length"`) with a Quasar table showing arrangement details and progress bar. Add actions column to orange piller table with edit/forgive buttons. Add edit dialog (q-dialog) with reroute_percent input and save button. Add forgive confirmation dialog. Use same computed field pattern from S03 (remaining_debt, progress_percent in JS).
  - Verify: Code inspection confirms: merchant section with `v-if`, action buttons on piller table, edit dialog, forgive dialog, all JS methods present
  - Done when: Both views render conditionally, management controls call correct API endpoints

## Files Likely Touched

- `orangepiller/views_api.py`
- `orangepiller/models.py`
- `orangepiller/templates/orangepiller/index.html`
- `orangepiller/static/js/index.js`
- `tests/extensions/orangepiller/test_merchant_api.py`
