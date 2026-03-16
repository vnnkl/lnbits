---
id: T01
parent: S03
milestone: M001
provides:
  - Orange piller dashboard with arrangement table, progress bars, and status badges
key_files:
  - orangepiller/templates/orangepiller/index.html
  - orangepiller/static/js/index.js
key_decisions:
  - Computed remaining_debt and progress_percent in JS (not from API) to avoid Pydantic serialization issues with @property fields
  - Used progress_percent as string via toFixed(2) for display consistency, parsed as number for q-linear-progress
patterns_established:
  - LNbits extension dashboard pattern: wallet selector → watcher → API fetch → computed fields → q-table with custom slots
observability_surfaces:
  - Browser DevTools network tab shows GET /orangepiller/api/v1/arrangements on wallet change
  - API errors surface as Quasar toast notifications via LNbits.utils.notifyApiError
  - Empty state message distinguishes zero data from fetch failure
duration: 10m
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T01: Build orange piller dashboard with arrangement table and progress bars

**Replaced placeholder index.html with full Quasar dashboard showing arrangements in q-table with progress bars, status badges, and wallet-triggered data refresh.**

## What Happened

Replaced the placeholder `index.html` with a full Quasar dashboard template following the splitpayments extension pattern. Created `static/js/index.js` with a Vue 3 Options API app using `windowMixin`. The wallet selector triggers `getArrangements()` via a watcher, which calls `GET /orangepiller/api/v1/arrangements` with the wallet's adminkey. Response data is mapped to add computed `remaining_debt` (total - repaid) and `progress_percent` ((repaid/total * 100).toFixed(2)). The q-table uses custom column slots: `q-linear-progress` for the progress column and `q-chip` (green=completed, orange=active) for the status column. Empty state shows a friendly message when no arrangements exist.

## Verification

All 6 slice-level verification checks passed:
1. `grep -q 'q-table'` — template has table ✓
2. `grep -q 'q-linear-progress'` — progress bar present ✓
3. `grep -q 'LNbits.api.request'` — API call wired ✓
4. `grep -q 'selectedWallet'` — wallet selector bound ✓
5. `grep -q 'remaining_debt|progress_percent'` — computed fields in JS ✓
6. Node.js check: remaining_debt=55000, progress_percent='45.00' ✓

## Diagnostics

- Browser DevTools → Network → filter `arrangements` to see API response
- Vue data: `remaining_debt` and `progress_percent` computed client-side from `total_debt_sats` and `repaid_sats`
- API errors shown as Quasar notifications (check browser console for details)
- Empty table with "No arrangements yet" = successful empty response (not error)

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `orangepiller/templates/orangepiller/index.html` — Full Quasar dashboard template with wallet selector, q-table, progress bars, status badges, and info sidebar
- `orangepiller/static/js/index.js` — Vue 3 app with windowMixin, wallet watcher, API fetch, computed fields, and table column definitions
- `.gsd/milestones/M001/slices/S03/S03-PLAN.md` — Added Observability / Diagnostics section
- `.gsd/milestones/M001/slices/S03/tasks/T01-PLAN.md` — Added Observability Impact section
