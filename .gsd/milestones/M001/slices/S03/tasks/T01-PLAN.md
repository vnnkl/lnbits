---
estimated_steps: 5
estimated_files: 2
---

# T01: Build orange piller dashboard with arrangement table and progress bars

**Slice:** S03 — Orange piller dashboard
**Milestone:** M001

## Description

Replace the placeholder `index.html` with a full Quasar dashboard and create `static/js/index.js` with the Vue app that fetches arrangement data and renders it in a table with progress bars. This single task delivers the complete R005 requirement. Follows the splitpayments extension pattern exactly.

## Steps

1. Replace `orangepiller/templates/orangepiller/index.html` with full Quasar template:
   - Extend `base.html`, import `window_vars` macro
   - `{% block page %}`: wallet selector (`q-select` bound to `selectedWallet`, options from `g.user.wallets`), arrangement `q-table` with columns defined in JS, custom column slots for progress bar (`q-linear-progress`) and status badge (`q-chip`), empty state row when no arrangements
   - `{% block scripts %}`: call `window_vars(user)`, load JS via `<script src="/orangepiller/static/js/index.js"></script>`

2. Create `orangepiller/static/js/index.js` with Vue 3 Options API app:
   - `Vue.createApp` with `windowMixin`
   - `data()`: `selectedWallet: null`, `arrangements: []`, `columns` array defining q-table columns
   - `watch: { selectedWallet() { this.getArrangements() } }`
   - `methods.getArrangements()`: call `LNbits.api.request('GET', '/orangepiller/api/v1/arrangements', this.selectedWallet.adminkey)`, map response to add computed `remaining_debt` (total - repaid) and `progress_percent` ((repaid/total * 100).toFixed(2))
   - Mount with `app.mount('#vue')`

3. Define q-table columns: merchant_wallet (label "Merchant"), total_debt_sats ("Total Debt (sats)"), repaid_sats ("Repaid (sats)"), remaining_debt ("Remaining (sats)"), progress_percent ("Progress"), reroute_percent ("Reroute %"), status ("Status"), created_at ("Created")

4. Add custom template slots in index.html:
   - Progress column: `q-linear-progress` with `:value="props.row.progress_percent / 100"` and percentage label
   - Status column: `q-chip` — green "Completed" or orange "Active" based on `props.row.status`

5. Run all verification commands from the slice plan to confirm correctness.

## Must-Haves

- [ ] q-table renders arrangement data with all specified columns
- [ ] q-linear-progress shows payback progress visually
- [ ] Status distinguished via colored q-chip (active=orange, completed=green)
- [ ] remaining_debt and progress_percent computed in JavaScript, not expected from API
- [ ] Wallet selector triggers arrangement refresh (splitpayments pattern)
- [ ] Empty state shown when no arrangements exist
- [ ] Uses LNbits.api.request with adminkey for API calls

## Verification

- `grep -q 'q-table' orangepiller/templates/orangepiller/index.html` — table present
- `grep -q 'q-linear-progress' orangepiller/templates/orangepiller/index.html` — progress bar present
- `grep -q 'LNbits.api.request' orangepiller/static/js/index.js` — API call wired
- `grep -q 'selectedWallet' orangepiller/static/js/index.js` — wallet selector bound
- JS computed fields produce correct values for known test inputs

## Inputs

- `orangepiller/templates/orangepiller/index.html` — existing placeholder to replace
- `orangepiller/views_api.py` — GET /api/v1/arrangements returns `list[Arrangement]` (fields: id, orange_piller_wallet, merchant_wallet, merchant_user_id, total_debt_sats, repaid_sats, reroute_percent, status, created_at)
- `orangepiller/views.py` — template renderer already wired to serve index.html
- `orangepiller/__init__.py` — static files already mounted at `/orangepiller/static`
- Splitpayments reference: `/tmp/splitpayments/templates/splitpayments/index.html` and `/tmp/splitpayments/static/js/index.js`

## Expected Output

- `orangepiller/templates/orangepiller/index.html` — full Quasar dashboard template with q-table, progress bars, status badges, wallet selector
- `orangepiller/static/js/index.js` — Vue 3 app that fetches arrangements, computes derived fields, and drives the table

## Observability Impact

- **New signal**: `GET /orangepiller/api/v1/arrangements` network request visible in browser DevTools on every wallet selection change.
- **Error surfacing**: API errors shown as Quasar toast notifications via `LNbits.utils.notifyApiError(err)` — visible in UI and browser console.
- **Inspection**: Vue devtools or `document.querySelector('#vue').__vue_app__` exposes `arrangements` array with computed `remaining_debt` and `progress_percent` fields for debugging.
- **Empty state**: "No arrangements yet" message distinguishes "zero data" from "fetch failed" — the latter shows an error notification instead.
