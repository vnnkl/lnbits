---
estimated_steps: 5
estimated_files: 2
---

# T02: Add completion toast notification and cutover verification test

**Slice:** S05 — Clean cutover, notifications & packaging
**Milestone:** M001

## Description

R010 requires both parties to see a notification when debt is fully repaid. The dashboards already show "Completed" status badges, but there's no active notification when the transition happens. This task adds transition-aware toast notifications in JavaScript (comparing old vs new status on each data refresh) and writes a focused test file proving the cutover path: debt reaches zero → status becomes "completed" → subsequent payments are skipped.

## Steps

1. In `orangepiller/static/js/index.js`, modify `getArrangements()` to detect status transitions: before overwriting `this.arrangements`, iterate new data and compare against old `this.arrangements` by id — if any arrangement changed from non-"completed" to "completed", fire `this.$q.notify({type:'positive', message:'Arrangement completed! Debt fully repaid for merchant ' + id})`
2. Apply the same transition detection to `getMerchantArrangements()` for the merchant side — fire a toast when their arrangement completes
3. Create `tests/extensions/orangepiller/test_cutover.py` with tests:
   - `test_debt_completion_transitions_status`: call `update_arrangement_repaid` with sats that meet/exceed remaining debt, assert returned arrangement has `status == "completed"` and `repaid_sats == total_debt_sats`
   - `test_completed_arrangement_skipped`: mock an arrangement with `status="completed"`, call `on_invoice_paid`, assert no transfer was attempted
   - `test_exact_payoff_caps_and_completes`: arrangement with 1000 remaining, payment of 5000 at 50% (2500 reroute) — assert only 1000 is rerouted and status transitions to completed
4. Run tests and verify all pass
5. Verify toast code is present in index.js with grep

## Must-Haves

- [ ] Toast notification fires only on status *transition* to "completed", not when an already-completed arrangement is loaded
- [ ] Both piller and merchant views have transition detection
- [ ] test_cutover.py has at least 3 tests covering: status transition, skip logic, exact cap
- [ ] All tests pass

## Verification

- `python -m pytest tests/extensions/orangepiller/test_cutover.py -v` — all pass
- `grep -c 'notify' orangepiller/static/js/index.js` — shows notification calls exist
- Manual inspection: toast detection code compares old array status vs new, not just checks current status

## Inputs

- `orangepiller/static/js/index.js` — existing Vue app with `getArrangements()`, `getMerchantArrangements()`, `_mapArrangement()`
- `orangepiller/crud.py` — `update_arrangement_repaid` with atomic CASE cap and status transition
- `orangepiller/tasks.py` — `on_invoice_paid` with completed-arrangement skip
- `tests/extensions/orangepiller/test_reroute.py` — reference for mock patterns and test structure

## Observability Impact

- **New client-side signal:** Quasar toast notification (`$q.notify`) fires on arrangement status transition to "completed" — visible in browser UI only, not logged server-side
- **Inspection:** `_detectCompletionTransitions()` method in index.js compares old vs new arrangement arrays by id; only fires on *transition*, not on initial load of already-completed arrangements
- **Failure visibility:** If toast doesn't fire, check browser console for JS errors; verify `getArrangements()` / `getMerchantArrangements()` returns updated status from API
- **Test coverage:** `test_cutover.py` proves server-side cutover path (status transition, skip logic, cap behavior) — run with `python -m pytest tests/extensions/orangepiller/test_cutover.py -v`

## Expected Output

- `orangepiller/static/js/index.js` — modified with transition-aware toast notifications in both fetch methods
- `tests/extensions/orangepiller/test_cutover.py` — 3+ tests proving cutover path correctness
