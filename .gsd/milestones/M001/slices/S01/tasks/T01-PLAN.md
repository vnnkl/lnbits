---
estimated_steps: 8
estimated_files: 10
---

# T01: Extension scaffold with models, migration, and CRUD

**Slice:** S01 — Extension scaffold + onboarding API
**Milestone:** M001

## Description

Create the complete orangepiller extension skeleton following LNbits conventions (modeled on `/tmp/example/` and `/tmp/splitpayments/`). This includes all packaging files, the `Arrangement` domain model, the DB migration, all CRUD functions specified in the boundary map, and stub files for views, tasks, and templates that later slices will fill in.

## Steps

1. Create `config.json` with extension metadata (name "Orange Piller", short description, min_lnbits_version "1.0.0")
2. Create `manifest.json` with repo ID "orangepiller"
3. Create `pyproject.toml` based on example extension pattern
4. Create `models.py` with `Arrangement` (BaseModel: id, orange_piller_wallet, merchant_wallet, merchant_user_id, total_debt_sats, repaid_sats, reroute_percent, status, created_at) and `CreateArrangement` (BaseModel: total_debt_sats, reroute_percent). Add computed properties: `remaining_debt`, `progress_percent`, `is_completed`.
5. Create `migrations.py` with `m001_initial(db: Connection)` creating `orangepiller.arrangements` table. Use TEXT for IDs, INTEGER for sats/percent fields, TEXT for status with default "active", and `db.timestamp_now` for created_at default.
6. Create `crud.py` with `Database("ext_orangepiller")` and implement: `create_arrangement`, `get_arrangement`, `get_arrangements_by_piller`, `get_arrangement_by_merchant_wallet`, `update_arrangement_repaid`, `update_arrangement`
7. Create `__init__.py` with router prefix "/orangepiller", static files, start/stop lifecycle, `__all__` exports
8. Create stub `views.py` (template renderer), stub `tasks.py` (invoice listener skeleton), minimal `templates/orangepiller/index.html`

## Must-Haves

- [ ] `Arrangement` model has ALL fields from boundary map
- [ ] Computed properties `remaining_debt`, `progress_percent`, `is_completed` exist on `Arrangement`
- [ ] Migration creates schema-qualified table `orangepiller.arrangements`
- [ ] All four boundary CRUD functions exist: `get_arrangement_by_merchant_wallet`, `get_arrangements_by_piller`, `update_arrangement_repaid`, `update_arrangement`
- [ ] `create_arrangement` function exists for T02 to use
- [ ] Pydantic v1 conventions (no model_validator, no model_config, use @property for computed fields)
- [ ] `__init__.py` follows example extension pattern exactly

## Verification

- `python -c "from orangepiller.models import Arrangement, CreateArrangement; a = Arrangement(id='x', orange_piller_wallet='w1', merchant_wallet='w2', merchant_user_id='u1', total_debt_sats=1000, repaid_sats=500, reroute_percent=50, status='active', created_at='2024-01-01'); print(a.remaining_debt, a.progress_percent, a.is_completed)"`
- `python -c "from orangepiller.crud import get_arrangement_by_merchant_wallet, get_arrangements_by_piller, update_arrangement_repaid, update_arrangement, create_arrangement; print('all CRUD OK')"`
- `python -c "from orangepiller import orangepiller_ext; print(orangepiller_ext.prefix)"`

## Inputs

- `/tmp/example/` — Extension scaffold pattern (copy and rename)
- `/tmp/splitpayments/crud.py` — CRUD patterns with `Database("ext_splitpayments")`
- `/tmp/splitpayments/migrations.py` — Migration function signature and schema-qualified DDL
- S01-RESEARCH.md boundary map — exact field names and function signatures

## Observability Impact

- **New signals:** `loguru` logging in `tasks.py` on invoice payment with tag "orangepiller" (payment hash logged at INFO)
- **Inspection:** Future agents can verify the extension loads by importing `orangepiller.orangepiller_ext` and checking `.prefix == "/orangepiller"`. CRUD functions can be import-tested without DB.
- **Failure visibility:** Migration failures surface as DB errors on extension load. Model validation errors surface as Pydantic `ValidationError` with field-level detail. CRUD import failures indicate missing `lnbits.db` or `lnbits.helpers` dependencies.
- **Persisted state:** `orangepiller.arrangements` table with schema-qualified name. Rows have `status` field for lifecycle tracking and `repaid_sats` for progress auditing.

## Expected Output

- `__init__.py` — Extension entry point with router, static files, lifecycle
- `config.json` — Extension metadata
- `manifest.json` — GitHub repo reference
- `pyproject.toml` — Python packaging
- `models.py` — `Arrangement` and `CreateArrangement` models
- `migrations.py` — `m001_initial` creating `orangepiller.arrangements`
- `crud.py` — All CRUD functions for arrangement management
- `views.py` — Stub template view
- `tasks.py` — Stub invoice listener
- `templates/orangepiller/index.html` — Minimal template placeholder
