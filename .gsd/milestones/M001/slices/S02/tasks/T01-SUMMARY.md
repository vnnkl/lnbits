---
id: T01
parent: S02
milestone: M001
provides:
  - atomic debt update with cap and status transition in crud.py
  - complete payment rerouting handler in tasks.py with tag guard, cap, transfer, rollback
key_files:
  - orangepiller/crud.py
  - orangepiller/tasks.py
  - tests/extensions/orangepiller/test_reroute.py
key_decisions:
  - Used UPDATE+SELECT within db.connect() instead of RETURNING clause for SQLite compatibility
  - Rollback resets status to 'active' unconditionally (safe since it only fires after a failed transfer)
patterns_established:
  - Atomic SQL UPDATE with CASE for concurrent-safe field capping
  - try/except around create_invoice+pay_invoice with debt rollback on failure
observability_surfaces:
  - loguru INFO on each successful reroute (arrangement_id, payment_hash, reroute_sats, repaid, remaining, status)
  - loguru WARNING on pay_invoice failure with rollback details
  - loguru DEBUG on skip reasons (tag guard, no arrangement, zero amount, completed)
duration: 20m
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T01: Implement atomic debt update and payment rerouting flow

**Replaced naive debt update with atomic SQL cap + built complete payment rerouting handler with tag guard, transfer, and rollback**

## What Happened

Rewrote `update_arrangement_repaid` in crud.py to use a single SQL UPDATE with CASE expressions that cap `repaid_sats` at `total_debt_sats` and transition `status` to "completed" when fully repaid. Added `WHERE status = 'active'` guard. The UPDATE and subsequent SELECT both run inside `db.connect()` to hold the asyncio lock across the pair.

Added `rollback_arrangement_repaid` that decrements `repaid_sats` and resets status to "active" — used when `pay_invoice` fails after debt was already updated.

Implemented complete `on_invoice_paid` in tasks.py following the splitpayments pattern: tag guard → arrangement lookup → status check → cap calculation (`min(payment.sat * percent // 100, remaining_debt)`) → atomic debt update → `create_invoice(internal=True)` on orange piller wallet → `pay_invoice` from merchant wallet with `{"tag": "orangepiller"}` → rollback on failure.

Created test suite with 8 tests covering: successful reroute, tag guard skip, no-arrangement skip, completed-arrangement skip, zero-amount skip, cap-at-remaining-debt, rollback on payment failure, and sat-vs-msat verification.

## Verification

- `python -c "from orangepiller.crud import update_arrangement_repaid; print('ok')"` → ok
- `python -c "from orangepiller.tasks import on_invoice_paid; print('ok')"` → ok
- `python -m pytest tests/extensions/orangepiller/test_reroute.py -v` → 8/8 passed
- Code inspection: SQL UPDATE uses CASE for both `repaid_sats` and `status`
- Code inspection: `on_invoice_paid` has tag guard, arrangement lookup, cap calc, internal transfer, rollback

### Slice-level verification status (intermediate task — partial expected):
- ✅ `python -m pytest tests/extensions/orangepiler/test_reroute.py -v` — 8 passed
- ✅ Tests cover: atomic cap logic, zero-amount skip, completed arrangement skip, debt rollback, msat/sat boundary
- ✅ Code inspection: tasks.py follows splitpayments pattern with all required elements

## Diagnostics

- **Logs:** `grep "orangepiller: rerouted"` in loguru output confirms successful reroutes with full context.
- **Failures:** `grep "rolling back"` shows pay_invoice failures with exception details.
- **DB inspection:** `SELECT id, repaid_sats, total_debt_sats, status FROM orangepiller.arrangements` shows current debt state.

## Deviations

- Used `db.connect()` with UPDATE + separate SELECT instead of `RETURNING *` clause, per research recommendation for SQLite < 3.35 compatibility.
- Created test file as part of T01 (plan assigns it to T02) since it's needed for slice verification and tests validate the implementation.

## Known Issues

None.

## Files Created/Modified

- `orangepiller/crud.py` — Atomic `update_arrangement_repaid` with CASE cap + status transition; new `rollback_arrangement_repaid`
- `orangepiller/tasks.py` — Complete `on_invoice_paid` with tag guard, cap, internal transfer, rollback, structured logging
- `tests/extensions/orangepiller/__init__.py` — Test package init
- `tests/extensions/orangepiller/conftest.py` — sys.path fix for extension imports
- `tests/extensions/orangepiller/test_reroute.py` — 8 unit tests for reroute engine
- `tests/extensions/__init__.py` — Package init for test extensions directory
- `.gsd/milestones/M001/slices/S02/tasks/T01-PLAN.md` — Added Observability Impact section
