---
id: T03
parent: S01
milestone: M002
provides:
  - 9 tests proving TPoS integration happy path, graceful degradation, HTTP failure, merchant credentials, and extended model fields
key_files:
  - tests/extensions/orangepiller/test_tpos_onboarding.py
key_decisions:
  - Used inner `with patch` for httpx.AsyncClient (async context manager requires manual __aenter__/__aexit__ mocking) rather than @patch decorator
patterns_established:
  - _make_mock_user / _make_mock_httpx_response helpers for TPoS onboarding tests
  - _PATCH_PREFIX constant for consistent patch paths
observability_surfaces:
  - none (test-only task — no runtime changes)
duration: 15m
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T03: Add tests proving TPoS integration and graceful degradation

**9 tests covering TPoS provisioning happy path, absent/failure degradation, merchant credential surfacing, and extended CreateArrangement fields — all 29 tests pass.**

## What Happened

Created `tests/extensions/orangepiller/test_tpos_onboarding.py` with 9 tests organized into 5 test classes, following the existing mock-based pattern from M001 tests. The tests prove three risk retirements:

1. **Cross-extension HTTP calls** — `test_create_arrangement_with_tpos` and `test_httpx_called_with_tpos_payload` verify httpx POST to `/tpos/api/v1/tposs` with correct URL, adminkey header, and TPoS payload (merchant_name, currency, tax fields).
2. **Graceful degradation** — `test_create_arrangement_without_tpos` verifies TPoS-absent path (tpos_id=None, warning contains "not installed", httpx never called). `test_default_exts_omits_tpos_when_not_installed` verifies create_user_account called with only `["orangepiller"]`. `test_create_arrangement_tpos_http_failure` verifies httpx.HTTPError is caught, arrangement still created with warning.
3. **Merchant credentials always surfaced** — `test_merchant_credentials_format_with_tpos` and `test_merchant_credentials_format_without_tpos` verify `/wallet?usr={user_id}` URL is passed to create_arrangement regardless of TPoS status.

Additionally, `test_extended_create_fields_accepted` and `test_extended_create_fields_defaults` verify the CreateArrangement model accepts all 8 new fields and defaults gracefully.

## Verification

- `.venv/bin/python -m pytest tests/extensions/orangepiller/test_tpos_onboarding.py -v` — **9 passed**
- `.venv/bin/python -m pytest tests/extensions/orangepiller/ -v` — **29 passed** (20 existing M001 + 9 new S01)
- Slice verification: **all checks pass** — this is the final task in S01, and all slice verification criteria are met

## Diagnostics

None — this task adds only tests, no runtime code. Run `pytest tests/extensions/orangepiller/test_tpos_onboarding.py -v` to re-verify risk retirements.

## Deviations

- Plan called for 5+ tests; delivered 9 tests in 5 classes for finer coverage (added TPoS payload verification, default_exts verification, field defaults test).
- Used inner `with patch(...)` for httpx.AsyncClient instead of `@patch` decorator because async context manager mocking requires manual `__aenter__`/`__aexit__` setup that's cleaner inline.

## Known Issues

None

## Files Created/Modified

- `tests/extensions/orangepiller/test_tpos_onboarding.py` — 9 tests across 5 classes covering TPoS integration and graceful degradation
- `.gsd/milestones/M002/slices/S01/tasks/T03-PLAN.md` — Added missing Observability Impact section
- `.gsd/milestones/M002/slices/S01/S01-PLAN.md` — Marked T03 as complete
