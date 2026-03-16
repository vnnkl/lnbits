---
estimated_steps: 6
estimated_files: 1
---

# T03: Fiat reroute tests

**Slice:** S01 — Fiat reroute engine and data model
**Milestone:** M003

## Description

Write unit tests for the fiat reroute path with mocked exchange rates. Cover the happy path, cap logic, exact payoff, exchange rate failure, backward compatibility, and precision over many small payments.

## Steps

1. Create `tests/extensions/orangepiller/test_fiat_reroute.py` with test class structure
2. Write fixtures: a helper to create a fiat arrangement (e.g. EUR, €100, 50% reroute) and mock `satoshis_amount_as_fiat` / `fiat_amount_as_satoshis` to return deterministic values (e.g. 1 sat = €0.001, so 1000 sats = €1.00)
3. Test: fiat reroute happy path — 10,000 sat payment → €10 at mocked rate → 50% reroute → €5 fiat debt decremented → 5,000 sats transferred. Verify `repaid_fiat` incremented, `repaid_sats` unchanged (stays 0), correct sat transfer
4. Test: fiat cap at remaining debt — arrangement has €2.00 remaining, payment converts to €10 fiat → reroute capped at €2.00 → only €2.00 worth of sats transferred, status transitions to "completed"
5. Test: exchange rate failure — mock `satoshis_amount_as_fiat` to raise ValueError → reroute skipped, no debt change, no transfer attempted. Test: sat arrangement backward compat — `debt_currency="sat"` arrangement goes through existing sat path, `repaid_sats` updated, `repaid_fiat` untouched
6. Test: fiat precision — create €1.00 debt, 50% reroute, simulate 100 payments of 10 sats each (each worth €0.01 fiat). After 100 payments at 50% reroute = €0.005 per payment, 200 payments needed. Verify `repaid_fiat` accumulates correctly without drift

## Must-Haves

- [ ] Happy path test: fiat conversion, reroute, debt decrement, sat transfer
- [ ] Cap test: fiat reroute capped at remaining fiat debt, status transition
- [ ] Exchange rate failure test: skip reroute cleanly
- [ ] Backward compat test: sat arrangement uses sat path
- [ ] Precision test: many small fiat payments sum correctly
- [ ] All 32 existing tests still pass (no imports broken, no side effects)

## Verification

- `pytest tests/extensions/orangepiller/ -v` — all tests pass (32 existing + 5-6 new)
- `pytest tests/extensions/orangepiller/test_fiat_reroute.py -v` — new tests pass individually

## Inputs

- `orangepiller/tasks.py` — T02's fiat reroute engine to test
- `orangepiller/crud.py` — T01's fiat CRUD functions
- `orangepiller/models.py` — T01's fiat model fields
- `tests/extensions/orangepiller/test_reroute.py` — existing test patterns to follow (mock structure, fixture style)

## Expected Output

- `tests/extensions/orangepiller/test_fiat_reroute.py` — 5-6 test methods covering all fiat edge cases
