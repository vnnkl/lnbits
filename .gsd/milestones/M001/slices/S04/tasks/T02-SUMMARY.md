---
id: T02
parent: S04
milestone: M001
provides:
  - Merchant view section showing arrangement details when wallet is a merchant
  - Orange piller management controls (edit reroute %, forgive debt) with dialogs
  - getMerchantArrangements, updateArrangement, forgiveArrangement JS methods
key_files:
  - orangepiller/static/js/index.js
  - orangepiller/templates/orangepiller/index.html
key_decisions:
  - Merchant GET errors (404/empty) silently set merchantArrangements to [] — no false error toasts for non-merchant wallets
  - Extracted _mapArrangement() helper to DRY computed field mapping between piller and merchant views
  - Separate merchantColumns array for merchant table (shows orange_piller_wallet instead of merchant_wallet)
patterns_established:
  - Dialog state pattern: showXDialog bool + form data object, opened by method, closed on success or cancel
observability_surfaces:
  - Browser Network tab: GET /orangepiller/api/v1/merchant/arrangements on wallet switch
  - Browser Network tab: PUT /orangepiller/api/v1/arrangements/{id} on edit/forgive actions
  - Quasar toast notifications for API errors (403, 400) via notifyApiError
duration: 10m
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T02: Add merchant view section and management controls to dashboard

**Extended dashboard with conditional merchant view, edit/forgive action buttons, and two management dialogs wired to real PUT endpoints**

## What Happened

Extended `index.js` with: `merchantArrangements` array + `merchantLoading` flag, dialog state (`showEditDialog`, `editForm`, `showForgiveDialog`, `forgiveArrangementId`), `getMerchantArrangements()` calling merchant GET endpoint, `updateArrangement()` calling PUT with reroute_percent, `forgiveArrangement()` calling PUT with `{forgive: true}`, and shared `_mapArrangement()` helper for computed fields. Updated `selectedWallet` watcher to call both fetch methods. Added `merchantColumns` array for the merchant table (shows orange_piller_wallet instead of merchant_wallet). Added `actions` column to piller columns.

Extended `index.html` with: merchant section using `v-if="merchantArrangements.length"` with Quasar table + progress bars, actions column on piller table with edit (pencil) and forgive (heart) buttons gated on `status === 'active'`, edit reroute % dialog with number input (1–100 validation rules + hint), and forgive confirmation dialog with irreversible warning text.

## Verification

All must-haves confirmed via code inspection:
- ✅ `v-if="merchantArrangements.length"` on merchant section (line 111)
- ✅ Merchant table shows: total_debt, repaid, remaining, progress bar, reroute %, status via `merchantColumns`
- ✅ Action buttons (edit, forgive) on active arrangements (lines 81, 92)
- ✅ Edit dialog validates reroute_percent 1–100 and calls PUT (lines 207-208, method at line 193)
- ✅ Forgive dialog shows irreversible warning and calls PUT with `{forgive: true}` (line 245, method at line 217)
- ✅ Both views compute `remaining_debt` and `progress_percent` via `_mapArrangement()` (line 143-148)
- ✅ `watch.selectedWallet` calls both `getArrangements()` and `getMerchantArrangements()`
- ✅ Two `q-dialog` elements present (4 occurrences of q-dialog tag — open+close for each)
- ✅ Actions column in piller table columns (line 73)

### Slice-level verification:
- ✅ `pytest tests/extensions/orangepiller/test_merchant_api.py -v` — 6/6 passed
- ✅ PUT endpoint checks `key_info.wallet.id == arrangement.orange_piller_wallet`
- ✅ Merchant GET filters by `merchant_wallet`, not `orange_piller_wallet`
- ✅ index.html has conditional merchant section and management controls
- ✅ index.js has `getMerchantArrangements()`, `updateArrangement()`, `forgiveArrangement()` methods

All slice verification checks pass — S04 is complete.

## Diagnostics

- Browser Network tab: `GET /orangepiller/api/v1/merchant/arrangements` fires on every wallet switch
- Browser Network tab: `PUT /orangepiller/api/v1/arrangements/{id}` fires on edit save or forgive confirm
- API errors (403 unauthorized, 400 bad request) shown as Quasar toast notifications
- Merchant section only appears when merchantArrangements has data — non-merchant wallets see nothing extra
- Client-side validation on edit dialog prevents bad percent values from reaching server

## Deviations

- Added `_mapArrangement()` shared helper instead of duplicating mapping logic — cleaner than plan's "same pattern" suggestion
- Added separate `merchantColumns` array for merchant table instead of reusing piller columns — merchant sees orange_piller_wallet, not merchant_wallet
- Used `icon="favorite"` (heart) for forgive instead of exact "heart icon" — Quasar Material Icons equivalent

## Known Issues

None

## Files Created/Modified

- `orangepiller/static/js/index.js` — Extended with merchant data, management methods, dialog state, _mapArrangement helper, actions column, merchantColumns
- `orangepiller/templates/orangepiller/index.html` — Extended with merchant section, action column template, edit dialog, forgive confirmation dialog
- `.gsd/milestones/M001/slices/S04/tasks/T02-PLAN.md` — Added Observability Impact section (pre-flight fix)
