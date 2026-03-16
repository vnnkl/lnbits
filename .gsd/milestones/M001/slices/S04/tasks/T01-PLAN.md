---
estimated_steps: 6
estimated_files: 3
---

# T01: Implement merchant GET and arrangement PUT endpoints

**Slice:** S04 — Merchant view + arrangement management
**Milestone:** M001

## Description

Add the two API endpoints that S04 needs: a merchant-facing GET that returns arrangements where the authenticated wallet is the merchant_wallet, and a real PUT replacing the 501 stub with reroute_percent updates and debt forgiveness. Add the `UpdateArrangement` Pydantic request model. Write unit tests proving auth, validation, and business logic.

## Steps

1. Add `UpdateArrangement` model to `models.py` — `reroute_percent: Optional[int] = None`, `forgive: Optional[bool] = None`
2. Add `GET /api/v1/merchant/arrangements` endpoint to `views_api.py` — import `get_arrangement_by_merchant_wallet`, return arrangement as a list (wrap single result), use `require_admin_key` for auth, filter by `key_info.wallet.id`
3. Replace the PUT stub with real implementation:
   - Accept `UpdateArrangement` body and `arrangement_id` path param
   - `require_admin_key` for auth
   - Fetch arrangement via `get_arrangement(arrangement_id)`, 404 if not found
   - Check `arrangement.orange_piller_wallet == key_info.wallet.id`, 403 if not
   - If `data.forgive`: check status is active (400 if completed), call `update_arrangement(id, repaid_sats=arrangement.total_debt_sats, status="completed")`, log forgiveness
   - If `data.reroute_percent`: validate 1–100 (400), check status is active (400), call `update_arrangement(id, reroute_percent=data.reroute_percent)`, log change
   - Return updated arrangement
4. Add structured logging: INFO for successful updates with arrangement_id and action type
5. Write `tests/extensions/orangepiller/test_merchant_api.py` with tests:
   - `test_merchant_get_returns_own_arrangement` — mock CRUD, verify filtering
   - `test_put_rejects_unauthorized` — wallet ID mismatch → 403
   - `test_put_rejects_completed_arrangement` — status=completed → 400
   - `test_put_forgiveness` — sets repaid_sats and status correctly
   - `test_put_percent_update` — valid percent updates arrangement
   - `test_put_percent_validation` — percent outside 1–100 → 400

## Must-Haves

- [ ] Merchant GET endpoint returns only arrangements matching authenticated merchant_wallet
- [ ] PUT checks orange_piller_wallet ownership before any modification
- [ ] Forgiveness sets repaid_sats = total_debt_sats and status = "completed"
- [ ] Percent update rejected on completed arrangements
- [ ] All 6 tests pass

## Verification

- `pytest tests/extensions/orangepiller/test_merchant_api.py -v` — 6/6 pass
- `from orangepiller.models import UpdateArrangement` imports cleanly
- Route inspection: `orangepiller_ext_api` has 4 routes (POST, 2x GET, PUT)

## Observability Impact

- Signals added: loguru INFO on arrangement update with arrangement_id, action ("forgive" or "percent_change"), new values
- How a future agent inspects this: grep logs for "Arrangement updated"
- Failure state exposed: HTTP 403 for auth failure, HTTP 400 for invalid updates, logged at WARNING

## Inputs

- `orangepiller/views_api.py` — existing PUT stub to replace, GET pattern to follow
- `orangepiller/crud.py` — `get_arrangement`, `get_arrangement_by_merchant_wallet`, `update_arrangement` ready to use
- `orangepiller/models.py` — `Arrangement` and `CreateArrangement` models
- S01/S02 summaries — `@property` fields not in `.dict()`, `update_arrangement` uses `**kwargs`

## Expected Output

- `orangepiller/models.py` — `UpdateArrangement` model added
- `orangepiller/views_api.py` — merchant GET endpoint + real PUT endpoint with auth/validation/logging
- `tests/extensions/orangepiller/test_merchant_api.py` — 6 unit tests for endpoint logic
