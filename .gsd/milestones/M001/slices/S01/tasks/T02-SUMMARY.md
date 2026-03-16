---
id: T02
parent: S01
milestone: M001
provides:
  - POST /api/v1/arrangements endpoint with atomic merchant account creation
  - GET /api/v1/arrangements endpoint filtered by orange piller wallet
  - PUT /api/v1/arrangements/{id} stub (reserved for S04)
key_files:
  - orangepiller/views_api.py
  - orangepiller/__init__.py
key_decisions:
  - POST handler catches create_user_account_no_ckeck exceptions and returns 500 with logged details rather than letting them propagate raw
  - Input validation done explicitly via HTTPException before account creation to fail fast
patterns_established:
  - API endpoints use require_admin_key dependency for wallet authentication, key_info.wallet.id as the orange piller wallet identifier
observability_surfaces:
  - loguru INFO log on arrangement creation with arrangement_id, merchant_user_id, merchant_wallet_id
  - GET /api/v1/arrangements returns full arrangement state
  - HTTP 400 for invalid input, HTTP 500 with logged exception for account creation failures
duration: 10m
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T02: Onboarding API endpoints and integration verification

**Implemented three API endpoints (POST/GET/PUT) with atomic merchant account creation via `create_user_account_no_ckeck`**

## What Happened

Created `views_api.py` with the `orangepiller_ext_api` router containing three endpoints:

1. **POST /api/v1/arrangements** — Validates `CreateArrangement` input (total_debt_sats > 0, reroute_percent 1–100), calls `create_user_account_no_ckeck(default_exts=["orangepiller"])` to atomically create a merchant LNbits account with orangepiller auto-enabled, extracts `user.wallets[0].id` and `user.id`, creates the arrangement via CRUD, and returns full `Arrangement` with 201 status. Logs arrangement creation at INFO level.

2. **GET /api/v1/arrangements** — Uses `require_admin_key` dependency, filters arrangements by the authenticated wallet's ID via `get_arrangements_by_piller`.

3. **PUT /api/v1/arrangements/{arrangement_id}** — Stub returning 501 Not Implemented (reserved for S04).

Updated `__init__.py` to include `orangepiller_ext_api` in `__all__` exports. The router was already imported and included from T01's scaffold.

## Verification

- `python -c "from orangepiller.views_api import orangepiller_ext_api; print([r.path for r in orangepiller_ext_api.routes])"` → `['/api/v1/arrangements', '/api/v1/arrangements', '/api/v1/arrangements/{arrangement_id}']` ✅
- `python -c "from orangepiller import orangepiller_ext, orangepiller_ext_api; print('wired OK')"` → `wired OK` ✅
- Code inspection: POST handler imports and calls `create_user_account_no_ckeck` with `default_exts=["orangepiller"]` ✅
- Slice-level checks:
  - `from orangepiller.models import Arrangement, CreateArrangement` → models OK ✅
  - `from orangepiller.crud import get_arrangement_by_merchant_wallet, get_arrangements_by_piller, update_arrangement_repaid, update_arrangement` → crud OK ✅
  - Manual API test against running LNbits — not yet run (requires runtime, deferred to slice completion)
  - DB inspection — not yet run (requires runtime)

## Diagnostics

- **Inspect endpoints:** `python -c "from orangepiller.views_api import orangepiller_ext_api; print([r.path for r in orangepiller_ext_api.routes])"`
- **Inspect exports:** `python -c "from orangepiller import orangepiller_ext_api; print('OK')"`
- **Runtime logs:** Arrangement creation logs at INFO level: `Arrangement created: id=..., merchant_user_id=..., merchant_wallet_id=...`
- **Error shapes:** HTTP 400 with `detail` for invalid input; HTTP 500 with `detail` for account creation failures (exception logged via loguru)

## Deviations

None

## Known Issues

None

## Files Created/Modified

- `orangepiller/views_api.py` — Three API endpoints (POST, GET, PUT) with full onboarding logic replacing stub
- `orangepiller/__init__.py` — Added `orangepiller_ext_api` to `__all__` exports
