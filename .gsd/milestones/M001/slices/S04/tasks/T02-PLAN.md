---
estimated_steps: 5
estimated_files: 2
---

# T02: Add merchant view section and management controls to dashboard

**Slice:** S04 — Merchant view + arrangement management
**Milestone:** M001

## Description

Extend the existing S03 dashboard with: (1) a merchant section that shows the merchant's own arrangement details when logged in as a merchant, and (2) management controls on the orange piller table — edit reroute % and forgive debt — with dialogs and API calls.

## Steps

1. Extend `index.js` data: add `merchantArrangements: []`, `merchantLoading: false`, `showEditDialog: false`, `editForm: { id: '', reroute_percent: 50 }`, `showForgiveDialog: false`, `forgiveArrangementId: ''`
2. Add `getMerchantArrangements()` method: call `GET /orangepiller/api/v1/merchant/arrangements` with `selectedWallet.adminkey`, map response with computed fields (same pattern as `getArrangements`), store in `merchantArrangements`
3. Add `updateArrangement()` method: call `PUT /orangepiller/api/v1/arrangements/{id}` with `{ reroute_percent }` from `editForm`, notify success, close dialog, refresh arrangements
4. Add `forgiveArrangement()` method: call `PUT /orangepiller/api/v1/arrangements/{id}` with `{ forgive: true }`, notify success, close dialog, refresh arrangements
5. Update `watch.selectedWallet` to also call `getMerchantArrangements()`
6. In `index.html`: add merchant section after the orange piller section with `v-if="merchantArrangements.length"` — Quasar card with a simpler table showing total_debt, repaid, remaining, progress bar, reroute %, status
7. Add actions column to the orange piller Quasar table with edit (pencil icon) and forgive (heart icon) buttons, only shown when `status === 'active'`
8. Add `q-dialog` for editing reroute_percent: number input with min=1 max=100, save/cancel buttons
9. Add `q-dialog` for forgive confirmation: warning text explaining the action is irreversible, confirm/cancel buttons

## Must-Haves

- [ ] Merchant section conditionally renders only when merchantArrangements has data
- [ ] Merchant table shows: total debt, repaid, remaining, progress bar, reroute %, status
- [ ] Orange piller table has action buttons (edit, forgive) on active arrangements
- [ ] Edit dialog validates reroute_percent 1–100 and calls PUT
- [ ] Forgive dialog shows confirmation before calling PUT with forgive:true
- [ ] Both views compute remaining_debt and progress_percent client-side (Decision #6)

## Verification

- Code inspection: `index.html` contains `v-if="merchantArrangements.length"` section
- Code inspection: `index.js` has `getMerchantArrangements`, `updateArrangement`, `forgiveArrangement` methods
- Code inspection: action column exists in orange piller table columns and template
- Code inspection: two `q-dialog` elements exist (edit + forgive)
- Code inspection: `watch.selectedWallet` calls both `getArrangements()` and `getMerchantArrangements()`

## Inputs

- `orangepiller/templates/orangepiller/index.html` — S03 template with Quasar table
- `orangepiller/static/js/index.js` — S03 JS with `getArrangements()` pattern and computed field mapping
- T01 output — merchant GET and PUT endpoints available at expected paths

## Observability Impact

- **Client-side signals:** `getMerchantArrangements()` silently catches errors (404/empty) when wallet is not a merchant — no false error toasts. `updateArrangement()` and `forgiveArrangement()` surface API errors via `LNbits.utils.notifyApiError()` toast notifications.
- **Inspection surfaces:** Browser devtools Network tab shows `GET /orangepiller/api/v1/merchant/arrangements` on wallet switch (confirms merchant fetch fires). `PUT /orangepiller/api/v1/arrangements/{id}` visible on edit/forgive actions.
- **Failure visibility:** API errors (403 unauthorized, 400 invalid update) are shown as Quasar notification toasts via `notifyApiError`. Client-side validation prevents bad reroute_percent values from reaching the server.
- **How to verify later:** Open extension → switch wallets → check Network tab for merchant GET call. Click edit on active arrangement → change % → save → verify PUT call and success toast. Click forgive → confirm → verify PUT with `{forgive: true}` and arrangement disappears from active list.

## Expected Output

- `orangepiller/static/js/index.js` — Extended with merchant data, management methods, dialog state
- `orangepiller/templates/orangepiller/index.html` — Extended with merchant section, action buttons, edit/forgive dialogs
