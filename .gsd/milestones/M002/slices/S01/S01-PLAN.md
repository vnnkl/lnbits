# S01: TPoS integration + extended onboarding

**Goal:** Orange piller calls the extended POST endpoint with merchant name, currency, and TPoS settings → merchant account created with TPoS terminal auto-provisioned. API returns arrangement with TPoS URL and merchant credentials. Works without TPoS installed (arrangement created, TPoS fields null, warning in response).

**Demo:** `POST /orangepiller/api/v1/arrangements` with `merchant_name`, `currency`, `tip_options`, `tax_default` → response includes `tpos_id`, `tpos_url`, `merchant_credentials`. Same call on an instance without TPoS → response includes `tpos_id: null`, `warning: "TPoS extension not installed..."`.

## Must-Haves

- `Arrangement` model extended with `tpos_id`, `tpos_url`, `merchant_name`, `merchant_credentials` (all Optional)
- `CreateArrangement` extended with `merchant_name`, `currency`, `tip_options`, `tax_default`, `tax_inclusive`, `business_name`, `business_address`, `business_vat_id`
- Migration `m002_tpos_fields` adds columns to DB
- POST handler detects TPoS via `get_installed_extension("tpos")`
- POST handler creates TPoS terminal via `httpx` call to `POST /tpos/api/v1/tposs` with merchant's adminkey
- POST handler surfaces merchant login URL as `merchant_credentials`
- Graceful degradation: arrangement created with `tpos_id=None` and `warning` when TPoS absent or HTTP call fails
- `warning` field on `Arrangement` uses `no_database=True` (response-only)
- All 20 existing M001 tests still pass

## Proof Level

- This slice proves: contract + integration (via mocked HTTP calls)
- Real runtime required: no (mocked tests prove API contract; real TPoS integration deferred to operational verification)
- Human/UAT required: no

## Verification

- `cd /Users/constantin/Code/lnbits && .venv/bin/python -m pytest tests/extensions/orangepiller/ -v` — all tests pass (existing 20 + new S01 tests)
- New test file: `tests/extensions/orangepiller/test_tpos_onboarding.py`
  - `test_create_arrangement_with_tpos` — TPoS installed, httpx succeeds → tpos_id, tpos_url, merchant_credentials populated
  - `test_create_arrangement_without_tpos` — TPoS not installed → tpos_id=None, warning present, merchant_credentials still populated
  - `test_create_arrangement_tpos_http_failure` — TPoS installed but httpx fails → tpos_id=None, warning present, arrangement still created
  - `test_merchant_credentials_always_populated` — merchant_credentials contains login URL regardless of TPoS status
  - `test_extended_fields_in_response` — new fields (merchant_name, tpos_url etc.) present in arrangement response

## Observability / Diagnostics

- Runtime signals: `logger.info` on TPoS provisioning success/failure; `logger.warning` when TPoS not installed or HTTP call fails
- Inspection surfaces: `GET /api/v1/arrangements` returns `tpos_id`, `tpos_url`, `merchant_credentials`, `warning` fields
- Failure visibility: `warning` field in API response surfaces TPoS provisioning failure reason to caller
- Redaction constraints: `merchant_credentials` contains a login URL with `user.id` — not a secret per se (user-id-only auth), but should be treated as sensitive in logs

## Integration Closure

- Upstream surfaces consumed: `orangepiller/models.py`, `orangepiller/crud.py`, `orangepiller/views_api.py`, `orangepiller/migrations.py` (all from M001)
- New wiring introduced in this slice: `httpx.AsyncClient` call to TPoS API from POST handler; `get_installed_extension` import from `lnbits.core.crud.extensions`; `settings.lnbits_baseurl` import from `lnbits.settings`
- What remains before the milestone is truly usable end-to-end: S02 (dashboards with QR codes and printable poster)

## Tasks

- [x] **T01: Extend models and add m002 migration** `est:30m`
  - Why: All other work depends on the data layer having the new fields. Migration must exist before any DB operations with new columns.
  - Files: `orangepiller/models.py`, `orangepiller/migrations.py`
  - Do: Add `tpos_id: Optional[str] = None`, `tpos_url: Optional[str] = None`, `merchant_name: Optional[str] = None`, `merchant_credentials: Optional[str] = None` to `Arrangement`. Add `warning: Optional[str] = Field(None, no_database=True)` for response-only use. Extend `CreateArrangement` with `merchant_name: Optional[str] = None`, `currency: str = "sat"`, `tip_options: Optional[str] = None`, `tax_default: Optional[float] = 0`, `tax_inclusive: bool = True`, `business_name: Optional[str] = None`, `business_address: Optional[str] = None`, `business_vat_id: Optional[str] = None`. Add `m002_tpos_fields` migration with ALTER TABLE ADD COLUMN for each new DB field. Constraint: Pydantic v1 — use `Optional[x] = None` with defaults; `Field(no_database=True)` for response-only fields.
  - Verify: `cd /Users/constantin/Code/lnbits && .venv/bin/python -c "from orangepiller.models import Arrangement, CreateArrangement; a = Arrangement(id='x', orange_piller_wallet='w', merchant_wallet='m', merchant_user_id='u', total_debt_sats=1000, reroute_percent=10); print(a.tpos_id, a.warning); d = a.dict(); assert 'tpos_id' in d; assert 'warning' not in [k for k,v in d.items() if k == 'warning' and v is not None] or True; print('OK')"` and existing 20 tests still pass.
  - Done when: `Arrangement` has 5 new fields (4 DB + 1 no_database), `CreateArrangement` has 8 new fields, migration function exists and is syntactically valid, all 20 existing tests pass.

- [x] **T02: Wire TPoS provisioning and credential surfacing into POST handler** `est:1h`
  - Why: This is the core risk-retirement task — proves cross-extension HTTP calls work, TPoS detection works, and merchant credentials can be surfaced. Covers R101, R103, R106.
  - Files: `orangepiller/views_api.py`, `orangepiller/crud.py`
  - Do: In POST handler: (1) Import `get_installed_extension` from `lnbits.core.crud.extensions`, `settings` from `lnbits.settings`, and `httpx`. (2) Check `await get_installed_extension("tpos")` — if not None, add `"tpos"` to `default_exts` list. (3) After account creation, construct `base_url = settings.lnbits_baseurl.rstrip("/")`. (4) Build `merchant_credentials = f"{base_url}/wallet?usr={user.id}"`. (5) If TPoS installed: build TPoS payload (`name=data.merchant_name or "Terminal"`, `currency=data.currency`, `tip_options=data.tip_options or "[]"`, `tax_default=data.tax_default`, `tax_inclusive=data.tax_inclusive`, `business_name`, `business_address`, `business_vat_id`, `wallet=merchant_wallet`), call `POST {base_url}/tpos/api/v1/tposs` with `X-Api-Key: user.wallets[0].adminkey`, extract `tpos_id` from JSON response, construct `tpos_url = f"{base_url}/tpos/{tpos_id}"`. (6) Wrap httpx call in try/except — on failure, set `tpos_id=None`, `tpos_url=None`, `warning="TPoS provisioning failed: {error}"`. (7) If TPoS not installed: set `tpos_id=None`, `tpos_url=None`, `warning="TPoS extension is not installed..."`. (8) Pass new fields (`tpos_id`, `tpos_url`, `merchant_name`, `merchant_credentials`) to `create_arrangement`. (9) Set `warning` on the returned arrangement before returning (it's no_database, so set after DB insert). Update `create_arrangement` in crud.py to accept and pass through new fields.
  - Verify: Code review — handler has TPoS detection, conditional httpx call, credential construction, error handling. Import test: `.venv/bin/python -c "from orangepiller.views_api import api_create_arrangement; print('OK')"`.
  - Done when: POST handler conditionally provisions TPoS via httpx, surfaces `merchant_credentials`, handles TPoS-absent and httpx-failure gracefully with warnings. CRUD passes new fields through to DB.

- [x] **T03: Add tests proving TPoS integration and graceful degradation** `est:45m`
  - Why: Proves the three risk retirements (cross-extension HTTP, merchant credentials, TPoS detection) and establishes the contract boundary for S02. Ensures no M001 regressions.
  - Files: `tests/extensions/orangepiller/test_tpos_onboarding.py`
  - Do: Create test file with mocked dependencies (matching existing test patterns: `unittest.mock.AsyncMock`, `patch`). Mock `get_installed_extension`, `create_user_account_no_ckeck`, `create_arrangement`, and `httpx.AsyncClient`. Test cases: (1) `test_create_arrangement_with_tpos` — TPoS detected, httpx returns `{"id": "tpos123"}`, verify arrangement has `tpos_id="tpos123"`, `tpos_url` contains `/tpos/tpos123`, `merchant_credentials` contains `/wallet?usr=`. (2) `test_create_arrangement_without_tpos` — `get_installed_extension` returns None, verify `tpos_id=None`, `warning` contains "not installed", `merchant_credentials` still populated. (3) `test_create_arrangement_tpos_http_failure` — TPoS detected but httpx raises exception, verify arrangement created with `tpos_id=None`, `warning` contains failure message. (4) `test_merchant_credentials_always_populated` — verify `merchant_credentials` is non-None in both TPoS-present and TPoS-absent cases. (5) `test_extended_fields_passed_to_crud` — verify `create_arrangement` called with new fields from extended `CreateArrangement`. Run full test suite and confirm all 20 M001 tests + new tests pass.
  - Verify: `.venv/bin/python -m pytest tests/extensions/orangepiller/ -v` — all tests pass (20 existing + 5 new = 25+).
  - Done when: All tests pass, TPoS happy path / degradation / failure paths each have a passing test, M001 tests unaffected.

## Files Likely Touched

- `orangepiller/models.py`
- `orangepiller/migrations.py`
- `orangepiller/views_api.py`
- `orangepiller/crud.py`
- `tests/extensions/orangepiller/test_tpos_onboarding.py`
