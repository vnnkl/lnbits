---
id: S01
parent: M001
milestone: M001
provides:
  - Complete orangepiller extension scaffold with packaging files (config.json, manifest.json, pyproject.toml)
  - Arrangement and CreateArrangement Pydantic v1 models with computed properties (remaining_debt, progress_percent, is_completed)
  - m001_initial migration creating orangepiller.arrangements table with all fields and constraints
  - Full CRUD layer (create, get, list by piller, list by merchant wallet, update repaid, update flexible)
  - POST /api/v1/arrangements — atomic merchant account + wallet + arrangement creation via create_user_account_no_ckeck
  - GET /api/v1/arrangements — list arrangements for authenticated orange piller
  - PUT /api/v1/arrangements/{id} — stub (501) reserved for S04
  - Stub views.py, tasks.py, and minimal index.html template for downstream slices
requires: []
affects:
  - S02
  - S03
  - S04
  - S05
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
  - Used @property for computed fields (remaining_debt, progress_percent, is_completed) — Pydantic v1 doesn't support @computed_field; properties work but aren't in .dict() output
  - CRUD update_arrangement accepts **kwargs for flexible field updates — avoids per-field update functions
  - POST handler validates input explicitly before calling create_user_account_no_ckeck to fail fast on bad data
  - API uses require_admin_key dependency; key_info.wallet.id identifies the orange piller wallet
patterns_established:
  - Extension follows example/splitpayments pattern exactly — router prefix, static files, lifecycle hooks, __all__ exports
  - Schema-qualified tables (orangepiller.arrangements) with Database("ext_orangepiller")
  - Named SQL parameters (:param style) matching splitpayments CRUD pattern
  - API endpoints use require_admin_key for wallet authentication
observability_surfaces:
  - Import-test verification: models, CRUD, views_api, and __init__ all import cleanly without DB
  - loguru INFO log on arrangement creation with arrangement_id, merchant_user_id, merchant_wallet_id
  - GET /api/v1/arrangements returns full arrangement state including repaid_sats and status
  - HTTP 400 for invalid input, HTTP 500 with logged exception for account creation failures
  - tasks.py logs payment hash at INFO level for orangepiller-tagged invoices
drill_down_paths:
  - .gsd/milestones/M001/slices/S01/tasks/T01-SUMMARY.md
  - .gsd/milestones/M001/slices/S01/tasks/T02-SUMMARY.md
duration: 25m
verification_result: passed
completed_at: 2026-03-16
---

# S01: Extension scaffold + onboarding API

**Complete orangepiller extension with domain model, DB migration, CRUD layer, and atomic onboarding API that creates merchant account + wallet + arrangement in one call**

## What Happened

Built the orangepiller extension in two tasks:

**T01 (scaffold):** Created all 11 extension files following the example/splitpayments patterns. The `Arrangement` model has 9 persisted fields plus 3 computed properties (`remaining_debt`, `progress_percent`, `is_completed`). The migration creates `orangepiller.arrangements` with constraints (reroute_percent 0–100). CRUD provides 6 functions covering all boundary map contracts. Entry point wires the router at `/orangepiller` with static files and lifecycle hooks.

**T02 (API endpoints):** Implemented three endpoints on `orangepiller_ext_api`. The POST endpoint validates input, calls `create_user_account_no_ckeck(default_exts=["orangepiller"])` to atomically create a merchant LNbits account with the extension auto-enabled, extracts the wallet ID, creates the arrangement via CRUD, and returns the full arrangement with 201 status. GET filters by authenticated wallet. PUT is a 501 stub for S04.

## Verification

All slice-level verification checks pass:

- ✅ `from orangepiller.models import Arrangement, CreateArrangement` — models import cleanly
- ✅ `from orangepiller.crud import get_arrangement_by_merchant_wallet, get_arrangements_by_piller, update_arrangement_repaid, update_arrangement` — all CRUD functions exist
- ✅ `from orangepiller.views_api import orangepiller_ext_api` — API router has 3 routes (POST, GET, PUT)
- ✅ `from orangepiller import orangepiller_ext, orangepiller_ext_api` — extension wired correctly, prefix is `/orangepiller`
- ✅ Computed properties verified: `Arrangement(total_debt_sats=1000, repaid_sats=500, ...)` → `remaining_debt=500, progress_percent=50.0, is_completed=False`
- ✅ Code inspection: POST handler calls `create_user_account_no_ckeck` with `default_exts=["orangepiller"]`
- ⏳ Manual API test against running LNbits — deferred to UAT (requires runtime)
- ⏳ DB inspection of orangepiller.arrangements table — deferred to UAT (requires runtime)

## Requirements Advanced

- R001 (Merchant onboarding) — POST endpoint atomically creates merchant account + wallet + arrangement; `create_user_account_no_ckeck` called with `default_exts=["orangepiller"]` for auto-enable
- R002 (Payback arrangement configuration) — CreateArrangement model accepts total_debt_sats and reroute_percent (1–100); arrangement stored with all debt tracking fields
- R009 (Standalone extension packaging) — config.json, manifest.json, pyproject.toml created following standard LNbits extension structure

## Requirements Validated

- none — runtime verification needed to fully validate R001 (account creation from extension context)

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

None — both tasks followed the plan exactly.

## Known Limitations

- PUT /api/v1/arrangements/{id} returns 501 — implementation deferred to S04
- Computed properties (remaining_debt, progress_percent, is_completed) are Python @property, not in Pydantic .dict() output — API responses may need explicit serialization in S03/S04
- No runtime verification yet — account creation via create_user_account_no_ckeck has not been tested against a running LNbits instance
- tasks.py invoice listener is a skeleton — actual payment interception comes in S02

## Follow-ups

- S02 must wire the payment listener in tasks.py to intercept merchant payments and call update_arrangement_repaid
- S03/S04 must handle the @property serialization gap when returning arrangements to the frontend
- Runtime UAT should verify the full onboarding flow against a live LNbits instance to retire the account-creation risk

## Files Created/Modified

- `orangepiller/__init__.py` — Extension entry point with router, static files, lifecycle, __all__ exports
- `orangepiller/config.json` — Extension metadata (name, description, min LNbits version)
- `orangepiller/manifest.json` — GitHub repo reference for extension manager
- `orangepiller/pyproject.toml` — Python packaging configuration
- `orangepiller/models.py` — Arrangement (9 fields + 3 computed) and CreateArrangement models
- `orangepiller/migrations.py` — m001_initial creating orangepiller.arrangements table
- `orangepiller/crud.py` — 6 CRUD functions for arrangement lifecycle
- `orangepiller/views.py` — Stub template renderer
- `orangepiller/views_api.py` — POST/GET/PUT API endpoints with atomic onboarding
- `orangepiller/tasks.py` — Invoice listener skeleton
- `orangepiller/templates/orangepiller/index.html` — Minimal Quasar template placeholder

## Forward Intelligence

### What the next slice should know
- The `Arrangement` model's computed properties (`remaining_debt`, `progress_percent`, `is_completed`) are @property decorators, NOT Pydantic fields. They won't appear in `.dict()` or JSON serialization. S02 can use them in Python code directly; S03/S04 will need to handle serialization explicitly.
- `get_arrangement_by_merchant_wallet(wallet_id)` returns a single Arrangement or None — S02 uses this to check if an incoming payment's wallet has an active arrangement.
- `update_arrangement_repaid(arrangement_id, additional_sats)` does an atomic SQL increment of repaid_sats — S02 should call this but must also implement the `min(reroute_amount, remaining_debt)` cap logic before calling it.

### What's fragile
- `create_user_account_no_ckeck` is imported from `lnbits.core.services.users` — this function name has a typo ("ckeck" not "check") that exists in the LNbits codebase. If LNbits ever fixes the typo, the import breaks.
- The POST handler assumes `user.wallets[0]` exists after account creation — if `create_user_account_no_ckeck` ever returns a user without a default wallet, this will IndexError.

### Authoritative diagnostics
- Import tests are the fastest way to verify the extension is intact: `from orangepiller import orangepiller_ext, orangepiller_ext_api`
- Route inspection: `[r.path for r in orangepiller_ext_api.routes]` should show 3 paths
- Computed property test: instantiate Arrangement with known values and check remaining_debt, progress_percent, is_completed

### What assumptions changed
- No assumptions changed — the plan was accurate. `create_user_account_no_ckeck` exists with the expected signature and `default_exts` parameter.
