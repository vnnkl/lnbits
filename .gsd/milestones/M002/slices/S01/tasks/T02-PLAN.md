---
estimated_steps: 9
estimated_files: 2
---

# T02: Wire TPoS provisioning and credential surfacing into POST handler

**Slice:** S01 — TPoS integration + extended onboarding
**Milestone:** M002

## Description

Modify the POST `/api/v1/arrangements` handler to detect TPoS installation, conditionally create a TPoS terminal via internal httpx call, construct a merchant login URL, and handle failures gracefully. Update CRUD to pass through the new fields.

## Steps

1. In `views_api.py`, add imports: `httpx`, `json`, `get_installed_extension` from `lnbits.core.crud.extensions`, `settings` from `lnbits.settings`.
2. At the start of `api_create_arrangement`, check TPoS installation: `tpos_installed = await get_installed_extension("tpos")`.
3. Build `default_exts` list conditionally: `["orangepiller", "tpos"]` if `tpos_installed` else `["orangepiller"]` (Decision #12).
4. After account creation, construct `base_url = settings.lnbits_baseurl.rstrip("/")` and `merchant_credentials = f"{base_url}/wallet?usr={user.id}"`.
5. If TPoS installed, build the TPoS payload dict: `name` (from `data.merchant_name` or `"Terminal"`), `currency` (from `data.currency`), `tip_options` (from `data.tip_options` or `"[]"`), `tax_default` (from `data.tax_default`), `tax_inclusive` (from `data.tax_inclusive`), `business_name`, `business_address`, `business_vat_id`, `wallet` (merchant_wallet). Make `async with httpx.AsyncClient() as client:` POST to `{base_url}/tpos/api/v1/tposs` with `headers={"X-Api-Key": user.wallets[0].adminkey}`. Extract `tpos_id = resp_json["id"]` and construct `tpos_url = f"{base_url}/tpos/{tpos_id}"`.
6. Wrap the httpx call in try/except to catch any exception. On failure: `tpos_id = None`, `tpos_url = None`, `warning = f"TPoS provisioning failed: {str(exc)}"`. Log with `logger.warning`.
7. If TPoS not installed: `tpos_id = None`, `tpos_url = None`, `warning = "TPoS extension is not installed. Arrangement created without a payment terminal."`.
8. Update `create_arrangement` in `crud.py` to accept `tpos_id`, `tpos_url`, `merchant_name`, `merchant_credentials` and include them in the `Arrangement()` constructor call.
9. After `create_arrangement` returns, set `arrangement.warning = warning` (response-only field, not persisted) and return.

## Must-Haves

- [ ] TPoS detection via `get_installed_extension("tpos")` before any TPoS API call
- [ ] Conditional `default_exts` list (includes "tpos" only when installed)
- [ ] httpx POST to TPoS API with merchant's adminkey in `X-Api-Key`
- [ ] `merchant_credentials` contains login URL with user ID
- [ ] try/except around httpx call — failure doesn't prevent arrangement creation
- [ ] `warning` field populated when TPoS absent or httpx fails
- [ ] All new fields passed through CRUD to DB

## Verification

- `.venv/bin/python -c "from orangepiller.views_api import api_create_arrangement; print('Import OK')"` — no import errors
- Code review: handler has 3 code paths (TPoS OK, TPoS absent, TPoS error) each producing correct field values
- Existing 20 tests still pass

## Observability Impact

- Signals added: `logger.info` on successful TPoS provisioning (includes tpos_id); `logger.warning` on TPoS not installed or httpx failure
- How a future agent inspects this: check `warning` field in API response; grep logs for "TPoS provisioning"
- Failure state exposed: `warning` in response tells caller exactly why TPoS wasn't provisioned

## Inputs

- `orangepiller/models.py` — T01 output with extended `Arrangement` and `CreateArrangement`
- `orangepiller/crud.py` — existing `create_arrangement` function
- `orangepiller/views_api.py` — existing POST handler
- S01-RESEARCH.md — TPoS API contract, base URL pattern, adminkey auth, `tip_options` serialization

## Expected Output

- `orangepiller/views_api.py` — POST handler with TPoS detection, conditional httpx provisioning, credential construction, graceful degradation
- `orangepiller/crud.py` — `create_arrangement` accepts and stores new fields
