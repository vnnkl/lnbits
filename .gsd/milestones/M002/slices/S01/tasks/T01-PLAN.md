---
estimated_steps: 5
estimated_files: 2
---

# T01: Extend models and add m002 migration

**Slice:** S01 — TPoS integration + extended onboarding
**Milestone:** M002

## Description

Extend the `Arrangement` and `CreateArrangement` models with TPoS-related and merchant config fields, and add the `m002_tpos_fields` migration to add matching columns to the database. This is the prerequisite data layer for all TPoS provisioning logic.

## Steps

1. In `orangepiller/models.py`, add to `Arrangement`: `tpos_id: Optional[str] = None`, `tpos_url: Optional[str] = None`, `merchant_name: Optional[str] = None`, `merchant_credentials: Optional[str] = None`. Add `warning: Optional[str] = Field(None, no_database=True)` — import `Field` from `pydantic`.
2. In `orangepiller/models.py`, extend `CreateArrangement` with: `merchant_name: Optional[str] = None`, `currency: str = "sat"`, `tip_options: Optional[str] = None`, `tax_default: Optional[float] = 0`, `tax_inclusive: bool = True`, `business_name: Optional[str] = None`, `business_address: Optional[str] = None`, `business_vat_id: Optional[str] = None`.
3. In `orangepiller/migrations.py`, add `async def m002_tpos_fields(db: Connection)` with ALTER TABLE ADD COLUMN for `tpos_id TEXT DEFAULT NULL`, `tpos_url TEXT DEFAULT NULL`, `merchant_name TEXT DEFAULT NULL`, `merchant_credentials TEXT DEFAULT NULL`.
4. Verify model serialization: `Arrangement.dict()` includes DB fields but excludes `warning` (no_database). `CreateArrangement` accepts the new fields.
5. Run existing 20 tests to confirm no regressions.

## Must-Haves

- [ ] `Arrangement` has 4 new DB-mapped Optional fields + 1 `no_database` warning field
- [ ] `CreateArrangement` has 8 new fields for TPoS/merchant config
- [ ] `m002_tpos_fields` migration adds 4 columns with `DEFAULT NULL`
- [ ] `warning` field excluded from DB serialization via `no_database=True`
- [ ] All 20 existing tests pass unchanged

## Verification

- `.venv/bin/python -c "from orangepiller.models import Arrangement, CreateArrangement; from pydantic import Field; a = Arrangement(id='x', orange_piller_wallet='w', merchant_wallet='m', merchant_user_id='u', total_debt_sats=1000, reroute_percent=10); assert a.tpos_id is None; assert a.warning is None; d = a.dict(); assert 'tpos_id' in d; assert 'warning' in d; print('Model OK')"` — fields exist and serialize
- `.venv/bin/python -c "from orangepiller.models import CreateArrangement; c = CreateArrangement(total_debt_sats=1000, reroute_percent=10, merchant_name='Test Shop', currency='EUR'); print(c.dict()); print('CreateArrangement OK')"` — extended fields accepted
- `.venv/bin/python -m pytest tests/extensions/orangepiller/ -v` — 20 tests pass

## Inputs

- `orangepiller/models.py` — existing `Arrangement` (9 fields) and `CreateArrangement` (2 fields)
- `orangepiller/migrations.py` — existing `m001_initial`
- S01-RESEARCH.md — field names, types, Pydantic v1 constraints, `no_database` pattern

## Observability Impact

- **Signals changed:** No runtime signals in this task (data layer only). The new `warning` field with `no_database=True` establishes the response-only pattern used by T02 to surface TPoS provisioning status.
- **Inspection:** After migration, `SELECT tpos_id, tpos_url, merchant_name, merchant_credentials FROM orangepiller.arrangements` shows the new columns (all NULL until T02 populates them).
- **Failure visibility:** Migration failure would prevent extension startup — visible in LNbits startup logs as a migration error for `orangepiller`.

## Expected Output

- `orangepiller/models.py` — `Arrangement` with 14 fields (9 existing + 4 DB + 1 no_database), `CreateArrangement` with 10 fields (2 existing + 8 new)
- `orangepiller/migrations.py` — `m002_tpos_fields` function added
