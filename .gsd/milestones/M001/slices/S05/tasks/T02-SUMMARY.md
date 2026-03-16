---
id: T02
parent: S05
milestone: M001
provides:
  - Transition-aware completion toast notifications in both piller and merchant dashboards
  - Cutover verification test suite proving debt-zero → completed → skip path
key_files:
  - orangepiller/static/js/index.js
  - tests/extensions/orangepiller/test_cutover.py
key_decisions:
  - Extracted shared _detectCompletionTransitions() method comparing old vs new arrays by id, reused by both getArrangements and getMerchantArrangements
patterns_established:
  - Status transition detection pattern: snapshot old list, compare per-id after fetch, notify only on transition (not on initial load)
observability_surfaces:
  - Client-side Quasar toast notification on arrangement completion transition
  - test_cutover.py verifies server-side cutover path (run with pytest)
duration: 8m
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T02: Add completion toast notification and cutover verification test

**Added transition-aware toast notifications for arrangement completion and 3 cutover-path tests proving debt-zero → completed → skip**

## What Happened

Added a `_detectCompletionTransitions(oldList, newList, labelFn)` method to the Vue app that compares arrangement statuses before and after each API fetch. When any arrangement transitions from non-"completed" to "completed", a Quasar positive toast fires with a descriptive message. Both `getArrangements()` (piller view) and `getMerchantArrangements()` (merchant view) use this method.

Created `test_cutover.py` with 3 focused tests:
1. `test_debt_completion_transitions_status` — payment triggers atomic update, status becomes "completed", repaid_sats capped at total
2. `test_completed_arrangement_skipped` — completed arrangement causes immediate skip, no update or transfer
3. `test_exact_payoff_caps_and_completes` — 50% of 5000 = 2500 reroute, but only 1000 remaining → caps at 1000, completes

## Verification

- `python -m pytest tests/extensions/orangepiller/test_cutover.py -v` — **3/3 passed** (0.56s)
- `grep -c 'notify' orangepiller/static/js/index.js` — **7** (includes 2 new transition notifications)
- `grep -q 'notify' orangepiller/static/js/index.js && echo "notification OK"` — **passed**
- Manual inspection: `_detectCompletionTransitions` builds `oldStatusById` map from old array, checks each new item — only fires when old status exists AND was not "completed" AND new status is "completed"

### Slice-level verification (all pass — S05 is final task):
- `python -m pytest tests/extensions/orangepiller/test_cutover.py -v` — ✅ passed
- `config.json OK` — ✅ passed
- `tile OK` — ✅ passed
- `docs OK` — ✅ passed
- `notification OK` — ✅ passed
- Extension config import — not run (requires full LNbits runtime, deferred to UAT)

## Diagnostics

- Toast fires only on status *transition*, not on initial page load — if toast doesn't appear, check browser console for JS errors in `_detectCompletionTransitions`
- Test failures: run `python -m pytest tests/extensions/orangepiller/test_cutover.py -v` from .venv
- Server-side completion logs: look for `orangepiller: rerouted ... status=completed` in loguru output

## Deviations

- Task plan step 1 said to use `id` in the toast message; used `a.merchant_wallet` / `a.orange_piller_wallet` instead for more meaningful identification
- Tests exercise the cutover path through `on_invoice_paid` (integration-level mocks) rather than calling `update_arrangement_repaid` directly, since the CRUD function requires a real DB connection

## Known Issues

None

## Files Created/Modified

- `orangepiller/static/js/index.js` — Added `_detectCompletionTransitions()` method and integrated it into both `getArrangements()` and `getMerchantArrangements()`
- `tests/extensions/orangepiller/test_cutover.py` — New test file with 3 cutover-path tests
- `.gsd/milestones/M001/slices/S05/tasks/T02-PLAN.md` — Added Observability Impact section (pre-flight fix)
