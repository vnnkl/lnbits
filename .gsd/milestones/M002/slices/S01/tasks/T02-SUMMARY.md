---
id: T02
parent: S01
milestone: M002
provides:
  - POST handler with TPoS detection, conditional httpx provisioning, credential construction, graceful degradation
  - CRUD create_arrangement accepts and stores tpos_id, tpos_url, merchant_name, merchant_credentials
key_files:
  - orangepiller/views_api.py
  - orangepiller/crud.py
key_decisions:
  - TPoS payload passes wallet field explicitly even though TPoS overrides it from auth key — for clarity and forward-compat
  - warning field set after create_arrangement returns (not persisted) matching no_database=True pattern from T01
patterns_established:
  - Conditional default_exts based on get_installed_extension result
  - try/except around cross-extension httpx calls — failure populates warning, never blocks arrangement creation
observability_surfaces:
  - logger.info on successful TPoS provisioning (includes tpos_id, merchant_user_id)
  - logger.warning on TPoS not installed or httpx failure (includes merchant_user_id, error detail)
  - warning field in API response surfaces TPoS provisioning failure reason to caller
duration: 8m
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T02: Wire TPoS provisioning and credential surfacing into POST handler

**POST handler now detects TPoS installation, conditionally provisions a TPoS terminal via httpx, constructs merchant login URL, and degrades gracefully with warning on failure.**

## What Happened

Modified `views_api.py` POST handler with: (1) new imports for `httpx`, `get_installed_extension`, `settings`; (2) TPoS detection via `await get_installed_extension("tpos")`; (3) conditional `default_exts` list; (4) `merchant_credentials` URL construction using `settings.lnbits_baseurl`; (5) conditional httpx POST to TPoS API with merchant's adminkey; (6) try/except graceful degradation; (7) warning field population for TPoS-absent and httpx-failure paths. Updated `crud.py` `create_arrangement` to accept `tpos_id`, `tpos_url`, `merchant_credentials` and pass them to the `Arrangement` constructor along with `merchant_name` from `data`.

## Verification

- **Import check:** `.venv/bin/python -c "from orangepiller.views_api import api_create_arrangement; print('Import OK')"` — passed
- **Must-haves:** 14/14 automated source checks passed (TPoS detection, conditional default_exts, httpx POST with adminkey, merchant_credentials URL, try/except, warning on failure/absent, all fields passed through CRUD)
- **Existing tests:** All 20 tests pass (0.56s) — no regressions
- **Code review:** Handler has 3 code paths: (a) TPoS installed + httpx success → tpos_id/tpos_url populated, no warning; (b) TPoS not installed → tpos_id=None, warning about missing extension; (c) TPoS installed + httpx failure → tpos_id=None, warning with error detail

## Diagnostics

- Check `warning` field in POST `/api/v1/arrangements` response to see TPoS provisioning status
- Grep logs for `"TPoS provisioned"` (success) or `"TPoS provisioning failed"` (failure)
- `merchant_credentials` in response contains `/wallet?usr={user_id}` login URL
- `tpos_url` in response contains `/tpos/{tpos_id}` when provisioning succeeds

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `orangepiller/views_api.py` — Added httpx/settings/get_installed_extension imports; rewrote POST handler with TPoS detection, conditional provisioning, credential construction, graceful degradation
- `orangepiller/crud.py` — Extended create_arrangement signature with tpos_id, tpos_url, merchant_credentials params; passes them plus merchant_name to Arrangement constructor

## Slice Verification Status (partial — T02 is task 2 of 3)

| Check | Status |
|-------|--------|
| `pytest tests/extensions/orangepiller/ -v` — 20 existing tests pass | ✅ |
| `test_tpos_onboarding.py` — new test file exists | ❌ (expected — T03) |
| POST handler has TPoS detection + httpx provisioning + graceful degradation | ✅ |
| CRUD passes new fields through to DB | ✅ |
