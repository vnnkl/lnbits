---
estimated_steps: 4
estimated_files: 3
---

# T02: Write tests for reroute engine correctness

**Slice:** S02 — Payment rerouting engine
**Milestone:** M001

## Description

Write unit tests that prove the rerouting logic is correct without requiring a running LNbits instance. Tests use unittest.mock to patch DB and payment service calls, verifying the cap logic, skip conditions, rollback path, and sat/msat boundary.

## Steps

1. Create `tests/extensions/orangepiller/__init__.py` (empty) and `tests/extensions/orangepiller/test_reroute.py`.
2. Write cap logic tests: mock `get_arrangement_by_merchant_wallet` to return an active arrangement with known values. Mock `update_arrangement_repaid`, `create_invoice`, `pay_invoice`. Call `on_invoice_paid` with a mock Payment. Assert `update_arrangement_repaid` was called with `min(payment.sat * percent // 100, remaining_debt)`. Test cases: (a) normal reroute (remaining > reroute_amount), (b) final payment cap (remaining < reroute_amount), (c) exact payoff (remaining == reroute_amount).
3. Write skip condition tests: (a) payment with tag "orangepiller" → no arrangement lookup. (b) No arrangement for wallet → no transfer. (c) Arrangement status "completed" → no transfer. (d) Reroute amount rounds to 0 → no transfer.
4. Write rollback test: mock `pay_invoice` to raise an exception. Assert `rollback_arrangement_repaid` was called with the correct amount. Assert the exception is caught (no propagation).

## Must-Haves

- [ ] Test cap at remaining debt on final payment
- [ ] Test zero-amount skip
- [ ] Test tag guard (no infinite loop)
- [ ] Test completed arrangement skip
- [ ] Test rollback on pay_invoice failure
- [ ] All tests use mocks — no DB or LNbits runtime required

## Observability Impact

This task is test-only — no new runtime signals. The tests validate the observability built in T01:
- Successful reroute log (INFO): verified in `test_successful_reroute` via loguru output
- Rollback warning (WARNING): verified in `test_rollback_on_payment_failure` and `test_rollback_on_create_invoice_failure`
- Skip debug logs: verified in tag guard, no-arrangement, completed, and zero-amount tests
- Future agent inspection: run `pytest tests/extensions/orangepiller/test_reroute.py -v` to confirm reroute engine correctness

## Verification

- `python -m pytest tests/extensions/orangepiller/test_reroute.py -v` — all tests pass

## Inputs

- `orangepiller/tasks.py` — completed `on_invoice_paid` from T01
- `orangepiller/crud.py` — atomic `update_arrangement_repaid` and `rollback_arrangement_repaid` from T01
- `orangepiller/models.py` — `Arrangement` model

## Expected Output

- `tests/extensions/orangepiller/__init__.py` — empty init
- `tests/extensions/orangepiller/test_reroute.py` — 7+ test cases covering cap, skip, rollback
