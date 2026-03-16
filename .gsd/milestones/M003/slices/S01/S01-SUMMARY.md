---
id: S01
milestone: M003
provides:
  - Arrangement model with debt_currency, total_debt_fiat, repaid_fiat fields
  - Fiat-aware computed properties (remaining_debt_fiat, progress_percent, is_completed)
  - Migration m003_fiat_fields adding 3 columns to arrangements table
  - update_arrangement_repaid_fiat and rollback_arrangement_repaid_fiat CRUD
  - Dual-path reroute engine branching on debt_currency (sat unchanged, fiat uses spot rate)
  - Graceful exchange rate failure handling (skip reroute, log warning)
key_files:
  - orangepiller/models.py
  - orangepiller/migrations.py
  - orangepiller/crud.py
  - orangepiller/tasks.py
  - orangepiller/views_api.py
  - tests/extensions/orangepiller/test_fiat_reroute.py
key_decisions:
  - "debt_currency='sat' uses existing sat path unchanged; fiat path is a separate branch"
  - "Exchange rate failure skips reroute (merchant keeps full payment)"
  - "Fiat stored as float with full precision, rounded only on display"
  - "total_debt_sats=0 as sentinel for fiat-denominated arrangements"
patterns_established:
  - Dual-path reroute with _handle_fiat_reroute extracted function
  - Fiat atomic SQL UPDATE with CASE cap mirroring sat pattern
  - Conditional validation in POST handler based on debt_currency
drill_down_paths:
  - .gsd/milestones/M003/slices/S01/tasks/T01-PLAN.md
  - .gsd/milestones/M003/slices/S01/tasks/T02-PLAN.md
  - .gsd/milestones/M003/slices/S01/tasks/T03-PLAN.md
duration: 20m
verification_result: pass
completed_at: 2026-03-16
---

# S01: Fiat reroute engine and data model

**Fiat-denominated debt tracking with spot-rate conversion, atomic updates, graceful degradation, and 12 new tests — all 44 tests pass, sat path completely unchanged.**

## What Happened

**T01** added the data layer: 3 new fields on Arrangement (`debt_currency`, `total_debt_fiat`, `repaid_fiat`), 2 on CreateArrangement, the `m003_fiat_fields` migration, fiat-aware computed properties, and dual CRUD functions (`update_arrangement_repaid_fiat`, `rollback_arrangement_repaid_fiat`) mirroring the sat atomic pattern. The POST handler now validates fiat vs sat input and the forgive handler sets `repaid_fiat` for fiat arrangements.

**T02** wired the fiat reroute engine. A branch on `arrangement.debt_currency != "sat"` calls `_handle_fiat_reroute()` which: fetches spot rate via `satoshis_amount_as_fiat()` → applies reroute % in fiat space → caps at remaining fiat debt → converts back to sats via `fiat_amount_as_satoshis()` → atomic fiat debt update → internal sat transfer → rollback on failure. Exchange rate failures are caught and skip the reroute cleanly.

**T03** proved it all works: 12 new tests covering happy path, fiat cap, exact payoff with completion, exchange rate failure skip, transfer failure rollback, sat backward compatibility, and 6 model property tests. All 44 tests (32 existing + 12 new) pass in 0.73s.

## Deviations

None. Plan executed as written.

## Files Created/Modified

- `orangepiller/models.py` — 3 new fields on Arrangement, 2 on CreateArrangement, fiat-aware computed properties
- `orangepiller/migrations.py` — m003_fiat_fields migration
- `orangepiller/crud.py` — 2 new CRUD functions, updated create_arrangement with fiat fields
- `orangepiller/tasks.py` — fiat branch in on_invoice_paid, _handle_fiat_reroute function
- `orangepiller/views_api.py` — fiat validation in POST, fiat forgiveness in PUT
- `tests/extensions/orangepiller/test_fiat_reroute.py` — 12 fiat tests
