---
id: T01
parent: S01
milestone: M002
provides:
  - Extended Arrangement model with TPoS + merchant fields
  - Extended CreateArrangement model with 8 merchant config fields
  - m002_tpos_fields migration adding 4 nullable columns
key_files:
  - orangepiller/models.py
  - orangepiller/migrations.py
key_decisions:
  - Used `Field(None, no_database=True)` for warning field — matches LNbits core pattern (wallets.py, users.py) for response-only fields excluded from DB serialization
patterns_established:
  - no_database=True pattern for response-only fields on Arrangement model
observability_surfaces:
  - DB columns: tpos_id, tpos_url, merchant_name, merchant_credentials (all NULL until T02)
  - warning field available on Arrangement for response-only TPoS status messaging
duration: 10m
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T01: Extend models and add m002 migration

**Added 5 fields to Arrangement (4 DB-mapped + 1 response-only), 8 fields to CreateArrangement, and m002 migration for 4 new columns.**

## What Happened

Extended `Arrangement` with `tpos_id`, `tpos_url`, `merchant_name`, `merchant_credentials` (all `Optional[str] = None`, DB-mapped) and `warning` (`Optional[str] = Field(None, no_database=True)`, response-only). Extended `CreateArrangement` with 8 TPoS/merchant config fields: `merchant_name`, `currency`, `tip_options`, `tax_default`, `tax_inclusive`, `business_name`, `business_address`, `business_vat_id`. Added `m002_tpos_fields` migration with 4 ALTER TABLE ADD COLUMN statements, all `TEXT DEFAULT NULL`.

## Verification

- **Model serialization:** `Arrangement.dict()` includes all 14 fields. `warning` field has `no_database=True` flag confirmed via `field_info.extra`. `CreateArrangement` accepts all 10 fields with correct defaults.
- **Migration syntax:** `m002_tpos_fields` has 4 `ALTER TABLE ADD COLUMN` statements with `TEXT DEFAULT NULL`.
- **Existing tests:** All 20 tests pass unchanged (0.58s).

## Diagnostics

- `SELECT tpos_id, tpos_url, merchant_name, merchant_credentials FROM orangepiller.arrangements` — all NULL until T02 populates them
- `Arrangement.__fields__['warning'].field_info.extra['no_database']` → `True` — confirms DB exclusion

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `orangepiller/models.py` — Added 5 fields to Arrangement, 8 fields to CreateArrangement, imported Field from pydantic
- `orangepiller/migrations.py` — Added m002_tpos_fields migration function
- `.gsd/milestones/M002/slices/S01/tasks/T01-PLAN.md` — Added Observability Impact section (pre-flight fix)

## Slice Verification Status (partial — T01 is task 1 of 3)

| Check | Status |
|-------|--------|
| `pytest tests/extensions/orangepiller/ -v` — 20 existing tests pass | ✅ |
| `test_tpos_onboarding.py` — new test file exists | ❌ (expected — T03) |
