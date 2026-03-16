---
estimated_steps: 7
estimated_files: 4
---

# T01: Fiat data model, migration, and CRUD

**Slice:** S01 — Fiat reroute engine and data model
**Milestone:** M003

## Description

Add fiat-denominated debt fields to the Arrangement model, write the database migration, create fiat-specific CRUD operations for atomic debt updates, and update the POST API handler to accept fiat arrangements.

## Steps

1. Add `debt_currency` (str, default "sat"), `total_debt_fiat` (Optional[float], default None), `repaid_fiat` (float, default 0) to `Arrangement` model
2. Add `debt_currency` (str, default "sat") and `total_debt_fiat` (Optional[float], default None) to `CreateArrangement` model
3. Add computed properties: `remaining_debt_fiat` (returns `max(0, total_debt_fiat - repaid_fiat)` when total_debt_fiat is set) and update `progress_percent` to use fiat fields when `debt_currency != "sat"`
4. Write `m003_fiat_fields` migration: 3 ALTER TABLE ADD COLUMN statements for `debt_currency` (TEXT DEFAULT 'sat'), `total_debt_fiat` (REAL DEFAULT NULL), `repaid_fiat` (REAL DEFAULT 0)
5. Add `update_arrangement_repaid_fiat(id, fiat_amount)` — atomic SQL UPDATE with CASE cap at `total_debt_fiat`, status transition when `repaid_fiat >= total_debt_fiat`
6. Add `rollback_arrangement_repaid_fiat(id, fiat_amount)` — mirrors `rollback_arrangement_repaid` but for fiat fields
7. Update `create_arrangement()` to accept and store `debt_currency`, `total_debt_fiat`, `repaid_fiat`. Update the POST handler in `views_api.py` to pass fiat fields through; when `debt_currency != "sat"`, set `total_debt_sats = 0` as a sentinel

## Must-Haves

- [ ] `Arrangement` model has `debt_currency`, `total_debt_fiat`, `repaid_fiat` fields
- [ ] `CreateArrangement` accepts `debt_currency` and `total_debt_fiat`
- [ ] `m003_fiat_fields` migration adds 3 columns, existing rows get `debt_currency='sat'`
- [ ] `update_arrangement_repaid_fiat` caps at `total_debt_fiat` atomically
- [ ] `rollback_arrangement_repaid_fiat` rolls back fiat amount
- [ ] `progress_percent` returns fiat-based progress when `debt_currency != "sat"`
- [ ] All 32 existing tests pass unchanged

## Verification

- `pytest tests/extensions/orangepiller/ -v` — all 32 tests pass
- Import check: `from orangepiller.crud import update_arrangement_repaid_fiat, rollback_arrangement_repaid_fiat`

## Inputs

- `orangepiller/models.py` — current Arrangement and CreateArrangement models
- `orangepiller/crud.py` — current CRUD with `update_arrangement_repaid` pattern to mirror
- `orangepiller/migrations.py` — m001 and m002 as template for m003
- Decision #4: atomic SQL UPDATE pattern with CASE cap (reuse for fiat)

## Expected Output

- `orangepiller/models.py` — 3 new fields on Arrangement, 2 on CreateArrangement, updated computed properties
- `orangepiller/migrations.py` — m003_fiat_fields function
- `orangepiller/crud.py` — 2 new CRUD functions, updated create_arrangement
- `orangepiller/views_api.py` — POST handler passes fiat fields
