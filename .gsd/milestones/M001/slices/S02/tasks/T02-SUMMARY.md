---
id: T02
parent: S02
milestone: M001
provides:
  - 11 unit tests proving reroute engine correctness (cap, skip, rollback, exact payoff, race condition)
key_files:
  - tests/extensions/orangepiller/test_reroute.py
key_decisions:
  - Added exact-payoff, create_invoice failure rollback, and atomic-update-None race condition tests beyond T01 baseline
patterns_established:
  - Mock-only async test pattern with @patch decorators on tasks.py imports for full isolation
observability_surfaces:
  - none (test-only task; validates runtime observability built in T01)
duration: 10m
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T02: Write tests for reroute engine correctness

**Expanded test suite to 11 cases covering cap logic, all skip paths, rollback on both pay and create failures, exact payoff, and concurrent race condition**

## What Happened

T01 had already created 8 tests. T02 added 3 more to complete coverage of the task plan's must-haves:
1. `test_exact_payoff` — remaining debt equals reroute amount, verifies exact transfer and completion
2. `test_rollback_on_create_invoice_failure` — create_invoice raises, rollback fires, no propagation
3. `test_atomic_update_returns_none_skips_transfer` — simulates concurrent completion race (update returns None), verifies no transfer attempted

All 11 tests use AsyncMock patches — no DB or LNbits runtime required.

## Verification

- `python -m pytest tests/extensions/orangepiller/test_reroute.py -v` → 11/11 passed
- Must-have checklist:
  - ✅ Test cap at remaining debt on final payment (`test_cap_at_remaining_debt`)
  - ✅ Test zero-amount skip (`test_zero_amount_skips`)
  - ✅ Test tag guard (`test_tag_guard_skips_orangepiller_payments`)
  - ✅ Test completed arrangement skip (`test_completed_arrangement_skips`)
  - ✅ Test rollback on pay_invoice failure (`test_rollback_on_payment_failure`)
  - ✅ All tests use mocks — no DB or LNbits runtime required

### Slice-level verification (final task — all must pass):
- ✅ `python -m pytest tests/extensions/orangepiller/test_reroute.py -v` — 11 passed
- ✅ Tests cover: atomic cap logic, zero-amount skip, completed arrangement skip, debt rollback on payment failure, msat/sat boundary
- ✅ Code inspection: `tasks.py` follows splitpayments pattern with tag guard, arrangement lookup, cap calculation, transfer, debt update

## Diagnostics

Run `pytest tests/extensions/orangepiller/test_reroute.py -v` to verify reroute engine correctness. Test output includes loguru messages at DEBUG/INFO/WARNING confirming each code path is exercised.

## Deviations

None — T01 had created the initial test file, T02 expanded it as planned.

## Known Issues

None.

## Files Created/Modified

- `tests/extensions/orangepiller/test_reroute.py` — Added 3 test cases (exact payoff, create_invoice rollback, atomic update race condition); total 11 tests
- `.gsd/milestones/M001/slices/S02/tasks/T02-PLAN.md` — Added Observability Impact section
- `.gsd/milestones/M001/slices/S02/S02-PLAN.md` — Marked T02 as done
