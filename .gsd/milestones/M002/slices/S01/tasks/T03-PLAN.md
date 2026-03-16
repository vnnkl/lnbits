---
estimated_steps: 6
estimated_files: 1
---

# T03: Add tests proving TPoS integration and graceful degradation

**Slice:** S01 — TPoS integration + extended onboarding
**Milestone:** M002

## Description

Write tests that prove the three risk retirements from the milestone roadmap: cross-extension HTTP calls to TPoS, merchant credential surfacing, and TPoS installation detection with graceful degradation. Uses the same mock-based pattern as existing M001 tests.

## Steps

1. Create `tests/extensions/orangepiller/test_tpos_onboarding.py` with imports matching the existing test pattern (pytest, AsyncMock, MagicMock, patch).
2. Create helper `_make_mock_user(user_id, wallet_id, adminkey)` that returns a MagicMock User with `id`, `wallets[0].id`, `wallets[0].adminkey`.
3. Create helper `_make_mock_httpx_response(tpos_id)` that returns a mock response with `.json()` returning `{"id": tpos_id}` and `.raise_for_status()` doing nothing.
4. Write `test_create_arrangement_with_tpos`: patch `get_installed_extension` (returns non-None), `create_user_account_no_ckeck` (returns mock user), `create_arrangement` (returns arrangement with tpos fields), and `httpx.AsyncClient` (mock POST returns tpos response). Call handler. Assert: `create_arrangement` called with `tpos_id`, `tpos_url`, `merchant_credentials`. Assert httpx POST was called with correct URL and adminkey header.
5. Write `test_create_arrangement_without_tpos`: patch `get_installed_extension` returning None. Call handler. Assert: `create_arrangement` called with `tpos_id=None`, `tpos_url=None`. Assert arrangement has `warning` containing "not installed". Assert `merchant_credentials` still populated. Assert `httpx.AsyncClient` was NOT called.
6. Write `test_create_arrangement_tpos_http_failure`: patch `get_installed_extension` (non-None), httpx raises `httpx.HTTPError`. Assert: arrangement created with `tpos_id=None`, `warning` contains failure info. Write `test_merchant_credentials_format`: verify `merchant_credentials` contains `/wallet?usr={user_id}`. Write `test_extended_create_fields_accepted`: construct `CreateArrangement` with all new fields, verify no validation error.

## Must-Haves

- [ ] Test for TPoS happy path — provisioning succeeds, fields populated
- [ ] Test for TPoS-absent path — graceful degradation with warning
- [ ] Test for TPoS HTTP failure — arrangement still created with warning
- [ ] Test that merchant credentials are always populated regardless of TPoS status
- [ ] All 20 existing M001 tests still pass alongside new tests
- [ ] Test pattern matches existing codebase (AsyncMock, patch decorators)

## Verification

- `.venv/bin/python -m pytest tests/extensions/orangepiller/test_tpos_onboarding.py -v` — all new tests pass
- `.venv/bin/python -m pytest tests/extensions/orangepiller/ -v` — all tests pass (20 existing + new)

## Inputs

- `orangepiller/views_api.py` — T02 output with TPoS provisioning logic
- `orangepiller/models.py` — T01 output with extended models
- `tests/extensions/orangepiller/test_merchant_api.py` — existing test pattern to follow
- `tests/extensions/orangepiller/conftest.py` — sys.path setup

## Observability Impact

- **No runtime observability changes** — this task adds only tests, not runtime code.
- **Test output signals**: pytest `-v` output shows per-test PASSED/FAILED status for each risk retirement (TPoS happy path, degradation, HTTP failure).
- **Future agent inspection**: Run `.venv/bin/python -m pytest tests/extensions/orangepiller/test_tpos_onboarding.py -v` to verify all three TPoS integration risk retirements still pass.
- **Log coverage**: Tests exercise all logger.info/warning paths from T02 (TPoS provisioned, TPoS not installed, TPoS provisioning failed) — visible in pytest output with `-s` flag.

## Expected Output

- `tests/extensions/orangepiller/test_tpos_onboarding.py` — 5+ tests covering TPoS provisioning happy/degradation/failure paths
