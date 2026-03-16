---
id: S02
parent: M001
milestone: M001
provides:
  - Complete payment rerouting engine: intercept merchant payments, calculate capped reroute, internal transfer, atomic debt tracking
  - Atomic debt update with CASE cap and status transition in crud.py
  - Debt rollback mechanism for failed transfers
  - 11 unit tests proving reroute correctness without runtime
requires:
  - slice: S01
    provides: Arrangement model, CRUD layer (get_arrangement_by_merchant_wallet, update_arrangement_repaid skeleton), tasks.py skeleton
affects:
  - S03
  - S04
  - S05
key_files:
  - orangepiller/crud.py
  - orangepiller/tasks.py
  - tests/extensions/orangepiller/test_reroute.py
key_decisions:
  - SQL UPDATE with CASE cap + SELECT within db.connect() context for SQLite compatibility (no RETURNING clause)
  - Debt updated before transfer attempt; rollback if pay_invoice or create_invoice fails
  - Rollback resets status to 'active' unconditionally (safe since only fires after failed transfer)
patterns_established:
  - Atomic SQL UPDATE with CASE for concurrent-safe field capping
  - try/except around create_invoice+pay_invoice with debt rollback on failure
  - Mock-only async test pattern with @patch decorators for full isolation
observability_surfaces:
  - loguru INFO on each successful reroute (arrangement_id, payment_hash, reroute_sats, repaid, remaining, status)
  - loguru WARNING on pay_invoice failure with rollback details
  - loguru DEBUG on skip reasons (tag guard, no arrangement, zero amount, completed)
  - DB inspection: SELECT id, repaid_sats, total_debt_sats, status FROM orangepiller.arrangements
drill_down_paths:
  - .gsd/milestones/M001/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/milestones/M001/slices/S02/tasks/T02-SUMMARY.md
duration: 30m
verification_result: passed
completed_at: 2026-03-16
---

# S02: Payment rerouting engine

**Built the core payment interception and rerouting engine with atomic debt tracking, exact cap logic, internal transfers, and rollback — proven by 11 unit tests**

## What Happened

Replaced the naive `update_arrangement_repaid` stub from S01 with an atomic SQL UPDATE using CASE expressions that cap `repaid_sats` at `total_debt_sats` and transition `status` to "completed" when fully repaid. The UPDATE and subsequent SELECT run inside `db.connect()` to hold the asyncio lock across both operations, preventing concurrent payment races. Added `rollback_arrangement_repaid` for reverting debt when transfers fail.

Implemented the complete `on_invoice_paid` handler in tasks.py following the LNbits splitpayments pattern: tag guard (skip payments tagged "orangepiller" to prevent infinite loops) → arrangement lookup by wallet_id → status check → cap calculation (`min(payment.sat * percent // 100, remaining_debt)`) → atomic debt update → `create_invoice(internal=True)` on orange piller wallet → `pay_invoice` from merchant wallet with tag → rollback on any failure. Structured logging at every decision point.

Built 11 unit tests covering: successful reroute, tag guard skip, no-arrangement skip, completed-arrangement skip, zero-amount skip, cap-at-remaining-debt, rollback on pay_invoice failure, exact payoff, rollback on create_invoice failure, atomic-update-returns-None race condition, and sat-vs-msat verification.

## Verification

- `.venv/bin/python -m pytest tests/extensions/orangepiller/test_reroute.py -v` → 11/11 passed
- `from orangepiller.crud import update_arrangement_repaid` → imports cleanly
- `from orangepiler.tasks import on_invoice_paid` → imports cleanly
- Code inspection: SQL UPDATE uses CASE for both `repaid_sats` and `status` with `WHERE status = 'active'` guard
- Code inspection: `on_invoice_paid` has tag guard, arrangement lookup, cap calc, internal transfer, rollback
- Tests cover all must-haves from slice plan: atomic cap logic, zero-amount skip, completed arrangement skip, debt rollback, msat/sat boundary

## Requirements Advanced

- R003 (Payment rerouting engine) — Core rerouting mechanic implemented: payment interception via invoice listener, percentage-based split, internal transfer, concurrency-safe via atomic SQL
- R004 (Exact debt tracking with final payment cap) — `min(reroute_amount, remaining_debt)` enforced on every payment; atomic SQL CASE caps at total_debt_sats
- R008 (Clean cutover) — Supporting: status transitions to "completed" when debt hits zero in the atomic update; completed arrangements skipped in Python and SQL

## Requirements Validated

- None yet — contract tests prove logic correctness but full validation requires integration testing on a running LNbits instance (S05 scope)

## New Requirements Surfaced

- None

## Requirements Invalidated or Re-scoped

- None

## Deviations

- T01 created the test file (plan assigned it to T02) since tests were needed for T01 verification. T02 then expanded the suite with 3 additional edge case tests.
- Used `db.connect()` with UPDATE + separate SELECT instead of `RETURNING *` clause, per research for SQLite < 3.35 compatibility.

## Known Limitations

- Concurrency safety relies on the asyncio lock within `db.connect()` — this serializes within a single LNbits process but would not protect across multiple worker processes (not a concern for typical LNbits deployments which are single-process)
- Rerouting is tested via mocks only — real payment flow integration testing deferred to runtime verification

## Follow-ups

- None — all planned work completed

## Files Created/Modified

- `orangepiller/crud.py` — Atomic `update_arrangement_repaid` with CASE cap + status transition; new `rollback_arrangement_repaid`
- `orangepiller/tasks.py` — Complete `on_invoice_paid` with tag guard, cap, internal transfer, rollback, structured logging
- `tests/extensions/__init__.py` — Package init for test extensions directory
- `tests/extensions/orangepiller/__init__.py` — Test package init
- `tests/extensions/orangepiller/conftest.py` — sys.path fix for extension imports
- `tests/extensions/orangepiller/test_reroute.py` — 11 unit tests for reroute engine

## Forward Intelligence

### What the next slice should know
- The `Arrangement` model uses Pydantic v1 `@property` for `remaining_debt`, `progress_percent`, `is_completed` — these won't appear in `.dict()` serialization. API responses need to add them explicitly or use a response model.
- `on_invoice_paid` is registered via `wait_for_paid_invoices` which uses `register_invoice_listener` with tag `"ext_orangepiller"` — this must be started in the extension's `__init__.py` or startup hook.

### What's fragile
- The `rollback_arrangement_repaid` resets status to `'active'` unconditionally — if a future slice adds more statuses (e.g. "paused"), this could incorrectly reactivate a paused arrangement. Currently safe since only "active" and "completed" exist.

### Authoritative diagnostics
- `SELECT id, repaid_sats, total_debt_sats, status FROM orangepiller.arrangements` — shows real-time debt state
- `grep "orangepiller:" *.log` — structured loguru messages at INFO/WARNING/DEBUG cover all code paths

### What assumptions changed
- Original plan assumed T01 and T02 would be sequential with separate test creation — in practice T01 built tests alongside implementation, and T02 expanded them. No impact on deliverables.
