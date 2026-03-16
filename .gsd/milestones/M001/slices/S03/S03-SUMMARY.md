---
id: S03
parent: M001
milestone: M001
provides:
  - Orange piller dashboard with arrangement table, progress bars, status badges, and wallet-triggered refresh
requires:
  - slice: S01
    provides: Arrangement model, GET /api/v1/arrangements endpoint, CRUD functions
  - slice: S02
    provides: Payment rerouting engine that populates repaid_sats data
affects:
  - S05
key_files:
  - orangepiller/templates/orangepiller/index.html
  - orangepiller/static/js/index.js
key_decisions:
  - Computed remaining_debt and progress_percent in JS (not from API) to avoid Pydantic v1 serialization issues with @property fields
  - Used progress_percent as string via toFixed(2) for display consistency, parsed as number for q-linear-progress
patterns_established:
  - LNbits extension dashboard pattern: wallet selector → watcher → API fetch → computed fields → q-table with custom slots
observability_surfaces:
  - Browser DevTools network tab shows GET /orangepiller/api/v1/arrangements on wallet change
  - API errors surface as Quasar toast notifications via LNbits.utils.notifyApiError
  - Empty state message distinguishes zero data from fetch failure
drill_down_paths:
  - .gsd/milestones/M001/slices/S03/tasks/T01-SUMMARY.md
duration: 10m
verification_result: passed
completed_at: 2026-03-16
---

# S03: Orange piller dashboard

**Replaced placeholder template with full Quasar dashboard showing all onboarded merchants with payback progress bars, computed debt tracking, status badges, and wallet-triggered data refresh.**

## What Happened

Replaced the placeholder `index.html` with a Quasar dashboard template following the splitpayments extension pattern. Created `static/js/index.js` with a Vue 3 Options API app using `windowMixin`. The wallet selector triggers `getArrangements()` via a watcher, which calls `GET /orangepiller/api/v1/arrangements` with the wallet's adminkey. Response data is enriched client-side with computed `remaining_debt` (total - repaid) and `progress_percent` ((repaid/total * 100).toFixed(2)). The q-table uses custom column slots: `q-linear-progress` for the progress column and `q-chip` (green=completed, orange=active) for the status column. Empty state shows "No arrangements yet" when no data exists.

## Verification

All 6 slice-level verification checks passed:
1. Template exists with `q-table` ✓
2. Progress bar (`q-linear-progress`) present ✓
3. JS uses `LNbits.api.request` for API calls ✓
4. Wallet selector (`selectedWallet`) wired ✓
5. Computed fields (`remaining_debt`, `progress_percent`) derived in JS ✓
6. Node.js correctness check: remaining_debt=55000, progress_percent='45.00' ✓

## Requirements Advanced

- R005 (Orange piller dashboard) — Fully delivered: dashboard lists all arrangements with progress bars, amounts, percentages, and status badges

## Requirements Validated

- None — R005 needs live runtime verification against a running LNbits instance with real arrangement data (UAT in S03-UAT.md)

## New Requirements Surfaced

- None

## Requirements Invalidated or Re-scoped

- None

## Deviations

None.

## Known Limitations

- No auto-refresh / polling — dashboard shows data as of last wallet selection. User must switch wallets or reload to see updated repayment progress.
- No sorting/filtering beyond q-table's built-in column sorting.

## Follow-ups

- None — S04 will add the merchant view and arrangement management controls.

## Files Created/Modified

- `orangepiller/templates/orangepiller/index.html` — Full Quasar dashboard template with wallet selector, q-table, progress bars, status badges, and info sidebar
- `orangepiller/static/js/index.js` — Vue 3 app with windowMixin, wallet watcher, API fetch, computed fields, and table column definitions

## Forward Intelligence

### What the next slice should know
- The dashboard template follows the splitpayments pattern exactly — S04's merchant view should follow the same structure but with a single-arrangement view instead of a table.
- `GET /orangepiller/api/v1/arrangements` returns raw `total_debt_sats` and `repaid_sats` — derived fields are computed in JS, not serialized from the API.

### What's fragile
- The JS computed fields assume `total_debt_sats > 0` — a zero-debt arrangement would show "100.00%" progress, which is technically correct but could confuse if such data exists.

### Authoritative diagnostics
- Browser DevTools → Network → filter `arrangements` to see raw API response and verify data shape.
- If the table shows no data, check: (1) network tab for 401 (bad key) vs 200 with empty array (no arrangements), (2) Quasar notification for API errors.

### What assumptions changed
- None — the slice executed exactly as planned.
