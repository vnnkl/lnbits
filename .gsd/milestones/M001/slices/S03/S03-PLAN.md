# S03: Orange piller dashboard

**Goal:** Orange piller opens the extension and sees all onboarded merchants with payback progress bars, amounts, percentages, and arrangement status.
**Demo:** Navigate to `/orangepiller` as an authenticated user with arrangements → q-table shows each merchant arrangement with progress bar, repaid/total amounts, reroute percentage, and active/completed status badge.

## Must-Haves

- Dashboard lists all arrangements for the selected wallet via `GET /orangepiller/api/v1/arrangements`
- Each row shows: total debt, repaid amount, remaining debt, progress bar, reroute percentage, status
- Remaining debt and progress percentage computed in JavaScript from `total_debt_sats` and `repaid_sats` (avoids touching Pydantic v1 serialization)
- Wallet selector for orange pillers with multiple wallets (standard LNbits pattern)
- Empty state when no arrangements exist
- Status visually distinguished (active vs completed)

## Verification

- `test -f orangepiller/templates/orangepiller/index.html && grep -q 'q-table' orangepiller/templates/orangepiller/index.html` — template exists with table
- `test -f orangepiller/static/js/index.js && grep -q 'LNbits.api.request' orangepiller/static/js/index.js` — JS fetches from API
- `grep -q 'remaining_debt\|progress_percent\|total_debt_sats - .*repaid_sats' orangepiller/static/js/index.js` — computed fields derived in JS
- `grep -q 'q-linear-progress' orangepiller/templates/orangepiller/index.html` — progress bar present
- `grep -q 'selectedWallet' orangepiller/static/js/index.js` — wallet selector wired
- Node.js inline check that JS computed fields are correct:
  ```bash
  node -e "
    const a = {total_debt_sats: 100000, repaid_sats: 45000};
    const rem = a.total_debt_sats - a.repaid_sats;
    const pct = (a.repaid_sats / a.total_debt_sats * 100).toFixed(2);
    console.assert(rem === 55000, 'remaining_debt wrong');
    console.assert(pct === '45.00', 'progress_percent wrong');
    console.log('computed fields OK');
  "
  ```

## Tasks

- [x] **T01: Build orange piller dashboard with arrangement table and progress bars** `est:30m`
  - Why: This is the entire slice — delivers R005 (Orange piller dashboard) by replacing the placeholder template with a full Quasar dashboard and creating the Vue.js app that fetches and renders arrangement data.
  - Files: `orangepiller/templates/orangepiller/index.html`, `orangepiller/static/js/index.js`
  - Do: Replace placeholder index.html with Quasar template extending base.html: wallet selector (q-select), arrangement q-table with columns for merchant wallet, total debt, repaid, remaining, progress (q-linear-progress), reroute %, status (q-chip), created date. Create static/js/index.js following splitpayments pattern: Vue.createApp with windowMixin, selectedWallet watcher, getArrangements method using LNbits.api.request('GET', '/orangepiller/api/v1/arrangements', wallet.adminkey), computed properties for remaining_debt and progress_percent derived from raw API fields. Add empty state message. Status badges: green chip for completed, orange for active.
  - Verify: All 6 verification commands from slice plan pass. Files follow splitpayments structural pattern.
  - Done when: Template renders a q-table with progress bars and status badges; JS fetches arrangements and computes derived fields; wallet selector triggers data refresh.

## Observability / Diagnostics

- **Browser console**: JS errors during `getArrangements()` surface as Quasar notifications via `LNbits.utils.notifyApiError(err)` — visible in the UI and browser console.
- **Network tab**: `GET /orangepiller/api/v1/arrangements` with `X-Api-Key` header — 200 returns `list[Arrangement]`, 401 means bad/missing adminkey.
- **Empty state**: When no arrangements exist, the table shows "No arrangements yet" — confirms the API returned an empty list (not an error).
- **Server logs**: `loguru` logs in `views_api.py` trace arrangement creation; GET endpoint logs nothing special but standard FastAPI request logs apply.
- **Inspection**: Open browser DevTools → Network → filter `arrangements` to see raw API response; compare `total_debt_sats` and `repaid_sats` with computed `remaining_debt` and `progress_percent` in the Vue data.

## Files Likely Touched

- `orangepiller/templates/orangepiller/index.html`
- `orangepiller/static/js/index.js`
