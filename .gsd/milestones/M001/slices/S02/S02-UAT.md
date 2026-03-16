# S02: Payment Rerouting Engine — UAT

**Milestone:** M001
**Written:** 2026-03-16

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: The rerouting engine is backend-only with no UI. All logic is testable via unit tests with mocks. Full integration testing with real payments is deferred to S05 runtime verification.

## Preconditions

- LNbits venv available at `.venv/bin/python`
- Extension source at `orangepiller/` in project root
- Test suite at `tests/extensions/orangepiller/test_reroute.py`
- No running LNbits instance required (all tests use mocks)

## Smoke Test

Run `cd /path/to/lnbits && .venv/bin/python -m pytest tests/extensions/orangepiller/test_reroute.py -v -o "addopts="` — all 11 tests should pass in under 1 second.

## Test Cases

### 1. Normal reroute (10% of 1000 sats)

1. Review `test_successful_reroute` — payment of 1000 sats to merchant with 10% reroute
2. Verify `update_arrangement_repaid` called with exactly 100 sats
3. Verify `create_invoice` called with `wallet_id=orange_piller_wallet`, `amount=100`, `internal=True`
4. Verify `pay_invoice` called with merchant wallet and orangepiller tag
5. **Expected:** 100 sats transferred, debt incremented by 100

### 2. Tag guard prevents infinite loop

1. Review `test_tag_guard_skips_orangepiller_payments` — payment with `extra.tag == "orangepiller"`
2. **Expected:** Handler returns immediately, no CRUD calls, no transfer

### 3. No arrangement for wallet

1. Review `test_no_arrangement_skips` — `get_arrangement_by_merchant_wallet` returns None
2. **Expected:** Handler returns without error, no update or transfer

### 4. Completed arrangement skipped

1. Review `test_completed_arrangement_skips` — arrangement with `status="completed"`
2. **Expected:** Handler returns without attempting reroute

### 5. Zero-amount reroute skipped

1. Review `test_zero_amount_skips` — 1% of 50 sats = 0
2. **Expected:** Handler returns without update or transfer (no zero-sat invoices)

### 6. Cap at remaining debt

1. Review `test_cap_at_remaining_debt` — 100% of 1000 sats but only 50 sats remaining
2. Verify `update_arrangement_repaid` called with 50 (not 1000)
3. **Expected:** Transfer capped at remaining debt, arrangement marked completed

### 7. Rollback on pay_invoice failure

1. Review `test_rollback_on_payment_failure` — `pay_invoice` raises exception
2. Verify `rollback_arrangement_repaid` called with correct arrangement_id and sats
3. **Expected:** Debt update reversed, no sat leakage, exception not propagated

### 8. Exact payoff (remaining == reroute)

1. Review `test_exact_payoff` — 10% of 1000 = 100 sats, remaining debt = 100 sats
2. Verify transfer amount is exactly 100 sats
3. **Expected:** Arrangement transitions to "completed", exact amount transferred

### 9. Rollback on create_invoice failure

1. Review `test_rollback_on_create_invoice_failure` — `create_invoice` raises
2. Verify `rollback_arrangement_repaid` called
3. **Expected:** Debt update reversed, no propagation

### 10. Race condition — concurrent completion

1. Review `test_atomic_update_returns_none_skips_transfer` — `update_arrangement_repaid` returns None
2. **Expected:** No `create_invoice` or `pay_invoice` called — silently skips

### 11. Uses payment.sat not payment.amount (msat)

1. Review `test_uses_payment_sat_not_msat` — payment.sat=50, payment.amount=50000
2. Verify reroute calculated as 10% of 50 = 5 sats (not 10% of 50000)
3. **Expected:** `update_arrangement_repaid` called with 5 sats

## Edge Cases

### Debt exactly equals reroute amount

1. Arrangement: total_debt=1000, repaid=900, reroute_percent=10
2. Payment: 1000 sats → reroute = min(100, 100) = 100
3. **Expected:** Exact payoff, status → "completed", no overpayment

### SQL CASE cap on overshoot

1. Inspect `update_arrangement_repaid` SQL: `repaid_sats + :sats > total_debt_sats → total_debt_sats`
2. **Expected:** `repaid_sats` never exceeds `total_debt_sats` regardless of input

### Rollback safety — status reset

1. Inspect `rollback_arrangement_repaid` SQL: always resets status to `'active'`
2. **Expected:** Safe because rollback only fires after debt was updated (status may have been set to "completed"), and the failed transfer means it should revert

## Failure Signals

- Any test failure in the 11-test suite
- `update_arrangement_repaid` SQL missing `WHERE status = 'active'` guard
- `on_invoice_paid` missing tag guard (`payment.extra.get("tag") == "orangepiller"`)
- `create_invoice` called without `internal=True`
- `pay_invoice` called without `extra={"tag": "orangepiller"}`
- Rollback not triggered on exception in transfer block
- Calculation using `payment.amount` (msat) instead of `payment.sat`

## Requirements Proved By This UAT

- R003 (Payment rerouting engine) — Tests prove: interception, percentage calculation, internal transfer, concurrency guard
- R004 (Exact debt tracking with final payment cap) — Tests prove: min(reroute, remaining) cap, exact payoff, SQL CASE cap
- R008 (Clean cutover, supporting) — Tests prove: status transitions to "completed" when debt hits zero

## Not Proven By This UAT

- Real payment flow on a running LNbits instance (integration testing in S05)
- Actual concurrent payments hitting the database simultaneously (unit tests mock the DB layer)
- Invoice listener registration and queue-based payment dispatch (wiring tested at runtime)
- UI visibility of rerouting events (S03/S04 scope)

## Notes for Tester

- All tests use `unittest.mock.AsyncMock` — no database or LNbits runtime needed
- The `conftest.py` adds the project root to `sys.path` so `orangepiller.*` imports resolve
- Run with `-o "addopts="` to override pyproject.toml's default args (which include `--cov` requiring extra plugins)
- The loguru logger outputs at DEBUG/INFO/WARNING during tests — this is expected and confirms code paths are exercised
