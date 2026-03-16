# S01: Extension scaffold + onboarding API — UAT

**Milestone:** M001
**Written:** 2026-03-16

## UAT Type

- UAT mode: mixed (artifact-driven for static checks + live-runtime for onboarding flow)
- Why this mode is sufficient: Static import checks prove the code structure is correct. Runtime API test against LNbits retires the critical risk (account creation from extension context).

## Preconditions

1. LNbits 1.5.x running locally (e.g. `lnbits --port 5000`)
2. orangepiller extension directory is in the LNbits extensions path or symlinked
3. orangepiller extension is installed/enabled on the instance
4. An orange piller user exists with at least one wallet — note their admin key (Settings → API Info)

## Smoke Test

```bash
uv run python -c "from orangepiller import orangepiller_ext, orangepiller_ext_api; print('OK')"
```
Should print `OK`. If this fails, the extension scaffold is broken.

## Test Cases

### 1. Models import and computed properties

1. Run: `uv run python -c "from orangepiller.models import Arrangement, CreateArrangement; a = Arrangement(id='x', orange_piller_wallet='w1', merchant_wallet='w2', merchant_user_id='u1', total_debt_sats=1000, repaid_sats=500, reroute_percent=50, status='active', created_at='2024-01-01'); print(a.remaining_debt, a.progress_percent, a.is_completed)"`
2. **Expected:** `500 50.0 False`

### 2. CRUD functions all importable

1. Run: `uv run python -c "from orangepiller.crud import get_arrangement_by_merchant_wallet, get_arrangements_by_piller, update_arrangement_repaid, update_arrangement, create_arrangement; print('all CRUD OK')"`
2. **Expected:** `all CRUD OK`

### 3. API router has correct routes

1. Run: `uv run python -c "from orangepiller.views_api import orangepiller_ext_api; print([(r.path, list(r.methods)) for r in orangepiller_ext_api.routes])"`
2. **Expected:** Three routes — POST `/api/v1/arrangements`, GET `/api/v1/arrangements`, PUT `/api/v1/arrangements/{arrangement_id}`

### 4. Create arrangement via POST (runtime)

1. Start LNbits with orangepiller extension enabled
2. Get the orange piller wallet's admin key
3. Run:
   ```bash
   curl -s -X POST http://localhost:5000/orangepiller/api/v1/arrangements \
     -H "X-Api-Key: <ADMIN_KEY>" \
     -H "Content-Type: application/json" \
     -d '{"total_debt_sats": 50000, "reroute_percent": 20}' | python -m json.tool
   ```
4. **Expected:** HTTP 201 response with JSON containing:
   - `id` — non-empty string
   - `orange_piller_wallet` — matches the wallet ID associated with the admin key
   - `merchant_wallet` — non-empty string (newly created wallet)
   - `merchant_user_id` — non-empty string (newly created user)
   - `total_debt_sats` — 50000
   - `repaid_sats` — 0
   - `reroute_percent` — 20
   - `status` — "active"
   - `created_at` — valid timestamp

### 5. List arrangements via GET (runtime)

1. Using the same admin key from test 4:
   ```bash
   curl -s http://localhost:5000/orangepiller/api/v1/arrangements \
     -H "X-Api-Key: <ADMIN_KEY>" | python -m json.tool
   ```
2. **Expected:** JSON array containing the arrangement created in test 4, with all fields matching

### 6. PUT stub returns 501 (runtime)

1. Using the arrangement ID from test 4:
   ```bash
   curl -s -o /dev/null -w "%{http_code}" -X PUT \
     http://localhost:5000/orangepiller/api/v1/arrangements/<ARRANGEMENT_ID> \
     -H "X-Api-Key: <ADMIN_KEY>" \
     -H "Content-Type: application/json" \
     -d '{}'
   ```
2. **Expected:** HTTP status code `501`

### 7. DB table exists with correct schema (runtime)

1. After running test 4, inspect the database:
   ```bash
   # For SQLite:
   sqlite3 <lnbits_data_dir>/database.sqlite3 ".schema 'orangepiller.arrangements'"
   ```
2. **Expected:** Table exists with columns: id, orange_piller_wallet, merchant_wallet, merchant_user_id, total_debt_sats, repaid_sats, reroute_percent, status, created_at

### 8. New merchant account has orangepiller extension enabled (runtime)

1. After test 4, log into LNbits as the newly created merchant user (use merchant_user_id from the POST response to look up or create a login)
2. Check the user's enabled extensions
3. **Expected:** orangepiller is in the merchant's enabled extensions list

## Edge Cases

### Invalid input — zero debt

1. ```bash
   curl -s -w "\n%{http_code}" -X POST http://localhost:5000/orangepiller/api/v1/arrangements \
     -H "X-Api-Key: <ADMIN_KEY>" \
     -H "Content-Type: application/json" \
     -d '{"total_debt_sats": 0, "reroute_percent": 20}'
   ```
2. **Expected:** HTTP 400 with error message about total_debt_sats

### Invalid input — reroute percent out of range

1. ```bash
   curl -s -w "\n%{http_code}" -X POST http://localhost:5000/orangepiller/api/v1/arrangements \
     -H "X-Api-Key: <ADMIN_KEY>" \
     -H "Content-Type: application/json" \
     -d '{"total_debt_sats": 50000, "reroute_percent": 150}'
   ```
2. **Expected:** HTTP 400 with error message about reroute_percent

### Missing auth header

1. ```bash
   curl -s -w "\n%{http_code}" http://localhost:5000/orangepiller/api/v1/arrangements
   ```
2. **Expected:** HTTP 401 or 403 (unauthorized)

### Multiple arrangements for same orange piller

1. Create two arrangements via POST with different debt amounts
2. GET /api/v1/arrangements
3. **Expected:** Both arrangements returned in the list

## Failure Signals

- Import errors on any orangepiller module → scaffold is broken
- POST returns 500 → `create_user_account_no_ckeck` failed (check logs for exception details)
- POST returns arrangement with empty merchant_wallet or merchant_user_id → account creation succeeded but wallet extraction failed
- GET returns empty array after successful POST → wallet ID filtering is wrong
- DB table missing → migration didn't run on startup

## Requirements Proved By This UAT

- R001 (Merchant onboarding) — Tests 4, 5, 8 prove atomic account + wallet + arrangement creation with auto-enabled extension
- R002 (Payback arrangement configuration) — Tests 4, edge cases prove sat-denominated debt and percentage configuration with validation
- R009 (Standalone extension packaging) — Smoke test + tests 1–3 prove extension loads as a standard LNbits extension

## Not Proven By This UAT

- R003 (Payment rerouting) — S02 scope
- R004 (Exact debt tracking with cap) — S02 scope
- R005 (Orange piller dashboard) — S03 scope
- R006 (Merchant transparency view) — S04 scope
- R007 (Arrangement management via PUT) — S04 scope (PUT is a 501 stub)
- R008 (Clean cutover) — S05 scope
- R010 (Repayment completion signal) — S05 scope
- Concurrent access to arrangements — S02 scope
- Extension installability from GitHub manifest — S05 scope

## Notes for Tester

- The `create_user_account_no_ckeck` function name is intentionally misspelled (missing 'h') — this matches the LNbits source code, not a bug in our extension
- The PUT endpoint returning 501 is intentional — it's a stub reserved for S04
- Computed properties (remaining_debt, progress_percent, is_completed) may not appear in API JSON responses since they're Python @property, not Pydantic fields — this is a known limitation to be addressed in S03/S04
- If LNbits startup fails after adding the extension, check that the orangepiller directory is in the correct extensions path and that config.json is valid JSON
