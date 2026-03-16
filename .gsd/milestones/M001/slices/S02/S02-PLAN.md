# S02: Payment rerouting engine

**Goal:** Incoming payments to a merchant's wallet are automatically split — the configured percentage is internally transferred to the orange piller's wallet, with exact debt tracking capped at the remaining balance, concurrency-safe.
**Demo:** Pay the merchant's wallet → configured percentage arrives in orange piller's wallet as internal transfer, debt decremented. Final payment caps exactly at remaining debt. Two rapid-fire payments don't overpay.

## Must-Haves

- Atomic debt update: single SQL UPDATE with cap logic and status transition to "completed" when debt hits zero
- Payment interception via `register_invoice_listener` with re-entrant tag guard (`"orangepiller"`)
- Internal transfer via `create_invoice(internal=True)` + `pay_invoice` following splitpayments pattern
- `payment.sat` used for calculations (not `payment.amount` which is msat)
- Zero-amount reroute skipped (when percentage rounds to 0 or remaining debt is 0)
- Completed arrangements skipped (both in Python check and SQL WHERE guard)
- Debt rollback if `pay_invoice` fails

## Proof Level

- This slice proves: integration
- Real runtime required: yes (for full proof — contract tests verify logic without runtime)
- Human/UAT required: no

## Verification

- `python -m pytest tests/extensions/orangepiller/test_reroute.py -v` — all tests pass
- Tests cover: atomic cap logic, zero-amount skip, completed arrangement skip, debt rollback on payment failure, msat/sat boundary
- Code inspection: `tasks.py` follows splitpayments pattern with tag guard, arrangement lookup, cap calculation, transfer, debt update

## Observability / Diagnostics

- Runtime signals: loguru INFO on each reroute (arrangement_id, payment_hash, reroute_sats, remaining_debt); WARNING on pay_invoice failure with rollback
- Inspection surfaces: `orangepiller.arrangements` table — repaid_sats and status columns reflect current state
- Failure visibility: pay_invoice failure logged with exception; debt rollback logged at WARNING level
- Redaction constraints: none

## Integration Closure

- Upstream surfaces consumed: `orangepiller/crud.py` (get_arrangement_by_merchant_wallet, update_arrangement_repaid), `orangepiller/models.py` (Arrangement), `lnbits.core.services` (create_invoice, pay_invoice), `lnbits.tasks` (register_invoice_listener)
- New wiring introduced in this slice: Full payment listener in tasks.py (skeleton from S01 → real implementation)
- What remains before the milestone is truly usable end-to-end: S03 (dashboard), S04 (merchant view + management), S05 (notifications + packaging)

## Tasks

- [x] **T01: Implement atomic debt update and payment rerouting flow** `est:45m`
  - Why: This is the core mechanic — intercept merchant payments, calculate capped reroute, transfer to orange piller, update debt atomically. Covers R003, R004, and R008 (supporting).
  - Files: `orangepiller/crud.py`, `orangepiller/tasks.py`
  - Do: (1) Replace `update_arrangement_repaid` with atomic version: UPDATE with CASE cap + status transition in SQL, wrapped in `db.connect()` context to hold lock across UPDATE+SELECT. (2) Implement `on_invoice_paid`: skip if tagged "orangepiller", lookup active arrangement by wallet_id, calculate `reroute_sats = min(payment.sat * percent // 100, remaining_debt)`, skip if 0, atomically update debt, create_invoice(internal=True) on orange piller wallet, pay_invoice from merchant wallet with tag. (3) Add debt rollback if pay_invoice raises. (4) Add structured logging at each decision point.
  - Verify: `from orangepiller.crud import update_arrangement_repaid` imports; `from orangepiller.tasks import on_invoice_paid` imports; code review confirms tag guard, cap logic, atomic SQL, rollback path.
  - Done when: tasks.py has complete rerouting flow with tag guard, cap, atomic update, transfer, rollback, and logging. crud.py has atomic update_arrangement_repaid with cap and status transition.

- [x] **T02: Write tests for reroute engine correctness** `est:30m`
  - Why: Proves R003 (rerouting works), R004 (exact cap), and concurrency safety without requiring a running LNbits instance.
  - Files: `tests/extensions/orangepiller/__init__.py`, `tests/extensions/orangepiller/test_reroute.py`
  - Do: (1) Create test directory and __init__.py. (2) Write unit tests using mock/patch for DB and payment services: test that reroute_sats calculation caps at remaining_debt; test that zero-amount payments are skipped; test that completed arrangements are skipped; test that pay_invoice failure triggers debt rollback; test msat vs sat boundary (payment.amount=5000 msat → payment.sat=5 → reroute calc uses 5). (3) Test the atomic SQL logic by verifying the CASE expression produces correct values for edge cases (repaid + amount > total, repaid + amount == total, repaid + amount < total).
  - Verify: `python -m pytest tests/extensions/orangepiller/test_reroute.py -v` passes all tests.
  - Done when: All tests pass, covering cap logic, zero skip, completed skip, rollback, and sat/msat boundary.

## Files Likely Touched

- `orangepiller/crud.py`
- `orangepiller/tasks.py`
- `tests/extensions/orangepiller/__init__.py`
- `tests/extensions/orangepiller/test_reroute.py`
