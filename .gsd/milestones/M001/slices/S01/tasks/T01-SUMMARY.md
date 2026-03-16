---
id: T01
parent: S01
milestone: M001
provides:
  - orangepiller extension scaffold with all packaging files
  - Arrangement and CreateArrangement Pydantic models with computed properties
  - m001_initial migration creating orangepiller.arrangements table
  - All CRUD functions for arrangement management (create, get, list, update)
  - Stub views, tasks, and template for downstream slices
key_files:
  - orangepiller/__init__.py
  - orangepiller/models.py
  - orangepiller/migrations.py
  - orangepiller/crud.py
  - orangepiller/views.py
  - orangepiller/views_api.py
  - orangepiller/tasks.py
  - orangepiller/config.json
  - orangepiller/manifest.json
  - orangepiller/pyproject.toml
  - orangepiller/templates/orangepiller/index.html
key_decisions:
  - Used @property for computed fields (remaining_debt, progress_percent, is_completed) per Pydantic v1 conventions
  - CRUD update_arrangement accepts **kwargs for flexible field updates
  - views_api.py is a stub — T02 implements the actual API endpoints
patterns_established:
  - Extension follows example/splitpayments pattern exactly — router prefix, static files, lifecycle hooks, __all__ exports
  - Schema-qualified tables (orangepiller.arrangements) with Database("ext_orangepiller")
  - Named SQL parameters (:param style) matching splitpayments CRUD pattern
observability_surfaces:
  - Import-test verification: models, CRUD, and __init__ all import cleanly without DB
  - tasks.py logs payment hash at INFO level for orangepiller-tagged invoices
  - Migration creates orangepiller.arrangements with status and repaid_sats for lifecycle auditing
duration: 15m
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T01: Extension scaffold with models, migration, and CRUD

**Created complete orangepiller extension skeleton with Arrangement domain model, DB migration, and all CRUD functions**

## What Happened

Built the full orangepiller extension scaffold by following the `/tmp/example/` and `/tmp/splitpayments/` patterns. Created all 11 files:

1. **Packaging**: `config.json` (extension metadata), `manifest.json` (repo ID), `pyproject.toml` (Python packaging)
2. **Domain model**: `models.py` with `Arrangement` (9 fields + 3 computed properties) and `CreateArrangement` (request model with total_debt_sats and reroute_percent)
3. **Migration**: `migrations.py` with `m001_initial` creating `orangepiller.arrangements` table with all fields, constraints (reroute_percent 0-100), and `db.timestamp_now` default for created_at
4. **CRUD**: `crud.py` with `Database("ext_orangepiller")` and 6 functions: `create_arrangement`, `get_arrangement`, `get_arrangements_by_piller`, `get_arrangement_by_merchant_wallet`, `update_arrangement_repaid`, `update_arrangement`
5. **Entry point**: `__init__.py` with router prefix `/orangepiller`, static files, start/stop lifecycle, `__all__` exports
6. **Stubs**: `views.py` (template renderer), `views_api.py` (empty API router for T02), `tasks.py` (invoice listener skeleton), `templates/orangepiller/index.html` (minimal Quasar page)

## Verification

All three task-level verification commands pass:

- `uv run python -c "from orangepiller.models import Arrangement, CreateArrangement; a = Arrangement(id='x', orange_piller_wallet='w1', merchant_wallet='w2', merchant_user_id='u1', total_debt_sats=1000, repaid_sats=500, reroute_percent=50, status='active', created_at='2024-01-01'); print(a.remaining_debt, a.progress_percent, a.is_completed)"` → `500 50.0 False` ✅
- `uv run python -c "from orangepiller.crud import get_arrangement_by_merchant_wallet, get_arrangements_by_piller, update_arrangement_repaid, update_arrangement, create_arrangement; print('all CRUD OK')"` → `all CRUD OK` ✅
- `uv run python -c "from orangepiller import orangepiller_ext; print(orangepiller_ext.prefix)"` → `/orangepiller` ✅

Slice-level verification (partial — T01 is intermediate):
- ✅ `from orangepiller.models import Arrangement, CreateArrangement` — models import cleanly
- ✅ `from orangepiller.crud import ...` — all CRUD functions exist
- ⏳ Manual API test — requires T02 (API endpoints not yet implemented)
- ⏳ DB inspection — requires running LNbits instance with extension loaded

## Diagnostics

- Import-test any module: `uv run python -c "from orangepiller.<module> import ..."`
- Computed properties testable without DB: instantiate `Arrangement` with known values, check `remaining_debt`, `progress_percent`, `is_completed`
- Migration syntax is validated by Python import; actual DDL execution happens on LNbits startup

## Deviations

None — followed the plan exactly.

## Known Issues

None.

## Files Created/Modified

- `orangepiller/__init__.py` — Extension entry point with router, static files, lifecycle
- `orangepiller/config.json` — Extension metadata (name, description, min version)
- `orangepiller/manifest.json` — GitHub repo reference
- `orangepiller/pyproject.toml` — Python packaging configuration
- `orangepiller/models.py` — Arrangement and CreateArrangement Pydantic models
- `orangepiller/migrations.py` — m001_initial creating orangepiller.arrangements table
- `orangepiller/crud.py` — All CRUD functions for arrangement management
- `orangepiller/views.py` — Stub template renderer view
- `orangepiller/views_api.py` — Stub API router (T02 fills in endpoints)
- `orangepiller/tasks.py` — Stub invoice listener skeleton
- `orangepiller/templates/orangepiller/index.html` — Minimal template placeholder
- `.gsd/milestones/M001/slices/S01/tasks/T01-PLAN.md` — Added Observability Impact section
