---
estimated_steps: 5
estimated_files: 2
---

# T02: Onboarding API endpoints and integration verification

**Slice:** S01 — Extension scaffold + onboarding API
**Milestone:** M001

## Description

Implement the three API endpoints that form the contract surface for downstream slices. The critical path is `POST /api/v1/arrangements` which atomically creates a merchant LNbits account (with orangepiller extension auto-enabled), extracts the new wallet ID, and stores the payback arrangement. This retires two key risks from the roadmap: account creation from extension context, and auto-enable on new accounts.

## Steps

1. Create `views_api.py` with `orangepiller_api_router = APIRouter()`
2. Implement `POST /api/v1/arrangements`: validate `CreateArrangement` input (total_debt_sats > 0, reroute_percent 1-100), call `create_user_account_no_ckeck(default_exts=["orangepiller"])`, extract `user.wallets[0].id` as merchant_wallet and `user.id` (from the account) as merchant_user_id, call `create_arrangement` from CRUD, return full `Arrangement` with 201 status
3. Implement `GET /api/v1/arrangements`: use `require_admin_key` dependency, call `get_arrangements_by_piller(wallet.wallet.id)`, return list
4. Implement `PUT /api/v1/arrangements/{arrangement_id}`: stub that returns 501 Not Implemented (S04 fills this in)
5. Update `__init__.py` to import and include `orangepiller_api_router`, verify all exports in `__all__`

## Must-Haves

- [ ] POST endpoint calls `create_user_account_no_ckeck` with `default_exts=["orangepiller"]`
- [ ] POST endpoint returns `Arrangement` including `merchant_user_id` and `merchant_wallet`
- [ ] POST endpoint uses `require_admin_key` for authentication (orange piller's wallet key)
- [ ] GET endpoint filters arrangements by the authenticated wallet's ID
- [ ] PUT endpoint exists (stub) so the router path is reserved for S04
- [ ] API router is wired into `__init__.py` and included in `__all__`
- [ ] Input validation: total_debt_sats > 0, reroute_percent between 1 and 100

## Verification

- `python -c "from orangepiller.views_api import orangepiller_api_router; print([r.path for r in orangepiller_api_router.routes])"` — shows all three endpoint paths
- Code inspection: POST handler imports and calls `create_user_account_no_ckeck`
- `python -c "from orangepiller import orangepiller_ext, orangepiller_api_router; print('wired OK')"` — confirms __init__.py exports

## Observability Impact

- Signals added/changed: loguru INFO log on successful arrangement creation with arrangement_id, merchant_user_id, merchant_wallet_id
- How a future agent inspects this: GET /api/v1/arrangements returns all arrangements with current state
- Failure state exposed: HTTP 400 for invalid input, HTTP 500 with logged exception for account creation failures

## Inputs

- `models.py` — `Arrangement` and `CreateArrangement` from T01
- `crud.py` — `create_arrangement`, `get_arrangements_by_piller` from T01
- `__init__.py` — Extension entry point from T01
- `lnbits/core/services/users.py` — `create_user_account_no_ckeck` function signature

## Expected Output

- `views_api.py` — Three API endpoints (POST, GET, PUT) with full onboarding logic
- `__init__.py` — Updated with API router import and inclusion
