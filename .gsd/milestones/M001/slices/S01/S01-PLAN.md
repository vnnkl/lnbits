# S01: Extension scaffold + onboarding API

**Goal:** Orange piller can create a merchant's LNbits account with the extension auto-enabled and a payback arrangement stored in DB, via a single API call.
**Demo:** `POST /orangepiller/api/v1/arrangements` with wallet admin key → returns arrangement with merchant user ID, wallet ID, debt amount, reroute percentage, and status "active". `GET /orangepiller/api/v1/arrangements` returns the arrangement list. DB contains the arrangement row.

## Must-Haves

- Extension installs and loads on LNbits (router mounts, static files, DB migration runs)
- `Arrangement` model with all fields from the boundary map (id, orange_piller_wallet, merchant_wallet, merchant_user_id, total_debt_sats, repaid_sats, reroute_percent, status, created_at)
- `POST /api/v1/arrangements` atomically creates merchant account + wallet + arrangement via `create_user_account_no_ckeck`
- `GET /api/v1/arrangements` returns arrangements for the authenticated orange piller
- `PUT /api/v1/arrangements/{id}` endpoint exists (stub body for S04)
- CRUD functions satisfy boundary contracts: `get_arrangement_by_merchant_wallet`, `get_arrangements_by_piller`, `update_arrangement_repaid`, `update_arrangement`
- New merchant account has orangepiller extension auto-enabled (`default_exts=["orangepiller"]`)

## Proof Level

- This slice proves: contract (DB schema, CRUD, API surface) + integration (account creation from extension context)
- Real runtime required: yes — must verify against running LNbits to retire account-creation risk
- Human/UAT required: no

## Verification

- `python -c "from orangepiller.models import Arrangement, CreateArrangement; print('models OK')"` — models import cleanly
- `python -c "from orangepiller.crud import get_arrangement_by_merchant_wallet, get_arrangements_by_piller, update_arrangement_repaid, update_arrangement; print('crud OK')"` — all CRUD functions exist
- Manual API test against running LNbits: POST creates arrangement, GET retrieves it, response includes merchant_user_id and merchant_wallet
- DB inspection: `orangepiller.arrangements` table exists with correct schema

## Observability / Diagnostics

- Runtime signals: `loguru` logging on arrangement creation (merchant account ID, wallet ID, arrangement ID)
- Inspection surfaces: `GET /api/v1/arrangements` returns full arrangement state including repaid_sats and status
- Failure visibility: HTTP 4xx/5xx with descriptive error messages on API failures; `create_user_account_no_ckeck` exceptions propagate as 500s with logged details
- Redaction constraints: merchant user IDs are not secrets but shouldn't be logged at INFO level in production

## Integration Closure

- Upstream surfaces consumed: `lnbits.core.services.users.create_user_account_no_ckeck`, `lnbits.db.Database`, `lnbits.helpers.urlsafe_short_hash`, `lnbits.decorators.require_admin_key`
- New wiring introduced: `orangepiller` extension router mounted at `/orangepiller`, DB schema `orangepiller.arrangements`
- What remains: S02 (payment rerouting engine), S03 (dashboard UI), S04 (merchant view + management), S05 (cutover + packaging)

## Tasks

- [x] **T01: Extension scaffold with models, migration, and CRUD** `est:45m`
  - Why: Creates the extension skeleton and all domain artifacts. Without this, there's nothing to mount an API on.
  - Files: `__init__.py`, `config.json`, `manifest.json`, `pyproject.toml`, `models.py`, `migrations.py`, `crud.py`, `views.py`, `tasks.py`, `templates/orangepiller/index.html`
  - Do: Copy structure from `/tmp/example/`, rename to `orangepiller`. Create `Arrangement` and `CreateArrangement` Pydantic v1 models. Write `m001_initial` migration creating `orangepiller.arrangements` table. Implement all CRUD functions from the boundary map. Create stub `views.py` with template renderer, stub `tasks.py` with invoice listener skeleton. Create minimal `index.html` template.
  - Verify: `python -c "from orangepiller.models import Arrangement, CreateArrangement"` and `python -c "from orangepiller.crud import get_arrangement_by_merchant_wallet, get_arrangements_by_piller, update_arrangement_repaid, update_arrangement"` both succeed
  - Done when: All files exist, models and CRUD import cleanly, migration function is syntactically valid

- [x] **T02: Onboarding API endpoints and integration verification** `est:45m`
  - Why: The onboarding endpoint is the critical risk — it must atomically create a merchant account + wallet + arrangement. This task also wires the GET and PUT endpoints that downstream slices consume.
  - Files: `views_api.py`, `__init__.py` (update router includes)
  - Do: Implement `POST /api/v1/arrangements` that validates `CreateArrangement`, calls `create_user_account_no_ckeck(default_exts=["orangepiller"])`, extracts wallet ID from returned User, creates Arrangement via CRUD, returns full arrangement including merchant_user_id. Implement `GET /api/v1/arrangements` filtering by orange piller wallet. Implement `PUT /api/v1/arrangements/{id}` as stub returning 501. Wire API router into `__init__.py`.
  - Verify: Import `orangepiller` package succeeds. POST/GET endpoints are registered on the router. Code review confirms `create_user_account_no_ckeck` is called with `default_exts=["orangepiller"]`.
  - Done when: `views_api.py` has all three endpoints, `__init__.py` exports the API router, POST handler calls `create_user_account_no_ckeck` and creates arrangement atomically

## Files Likely Touched

- `__init__.py`
- `config.json`
- `manifest.json`
- `pyproject.toml`
- `models.py`
- `migrations.py`
- `crud.py`
- `views.py`
- `views_api.py`
- `tasks.py`
- `templates/orangepiller/index.html`
- `static/` (tile image placeholder)
