---
id: S01
parent: M002
milestone: M002
provides:
  - Extended Arrangement model with tpos_id, tpos_url, merchant_name, merchant_credentials, warning (response-only)
  - Extended CreateArrangement model with 8 merchant/TPoS config fields
  - m002_tpos_fields migration adding 4 nullable columns
  - POST handler with TPoS detection, conditional httpx provisioning, credential surfacing, graceful degradation
  - CRUD create_arrangement accepts and stores new TPoS/merchant fields
  - 9 tests proving TPoS integration happy path, graceful degradation, HTTP failure, merchant credentials, extended fields
requires:
  - slice: M001/S01
    provides: Arrangement model, CreateArrangement model, CRUD, views_api POST handler, migrations infrastructure
affects:
  - M002/S02
key_files:
  - orangepiller/models.py
  - orangepiller/migrations.py
  - orangepiller/views_api.py
  - orangepiller/crud.py
  - tests/extensions/orangepiller/test_tpos_onboarding.py
key_decisions:
  - Used Field(None, no_database=True) for warning field — matches LNbits core pattern for response-only fields
  - TPoS as soft dependency via internal httpx calls — no direct Python imports from TPoS extension
  - Conditional default_exts — only include "tpos" when detected as installed
  - TPoS payload passes wallet field explicitly for clarity and forward-compat
  - warning field set after create_arrangement returns (not persisted) matching no_database=True pattern
  - try/except around cross-extension httpx calls — failure populates warning, never blocks arrangement creation
patterns_established:
  - no_database=True pattern for response-only fields on Arrangement model
  - Conditional default_exts based on get_installed_extension result
  - try/except around cross-extension httpx calls with graceful degradation
  - _make_mock_user / _make_mock_httpx_response helpers for TPoS onboarding tests
observability_surfaces:
  - logger.info on successful TPoS provisioning (includes tpos_id, merchant_user_id)
  - logger.warning on TPoS not installed or httpx failure (includes merchant_user_id, error detail)
  - warning field in API response surfaces TPoS provisioning failure reason to caller
  - merchant_credentials in response contains /wallet?usr={user_id} login URL
  - tpos_url in response contains /tpos/{tpos_id} when provisioning succeeds
drill_down_paths:
  - .gsd/milestones/M002/slices/S01/tasks/T01-SUMMARY.md
  - .gsd/milestones/M002/slices/S01/tasks/T02-SUMMARY.md
  - .gsd/milestones/M002/slices/S01/tasks/T03-SUMMARY.md
duration: 33m
verification_result: passed
completed_at: 2026-03-16
---

# S01: TPoS integration + extended onboarding

**POST /orangepiller/api/v1/arrangements now auto-provisions a TPoS terminal for the merchant via cross-extension httpx call, surfaces merchant login credentials, and degrades gracefully when TPoS is absent or HTTP call fails — proven by 9 new tests (29 total pass).**

## What Happened

**T01 (10m):** Extended `Arrangement` with 4 DB-mapped fields (`tpos_id`, `tpos_url`, `merchant_name`, `merchant_credentials`) and 1 response-only field (`warning` with `no_database=True`). Extended `CreateArrangement` with 8 merchant/TPoS config fields (`merchant_name`, `currency`, `tip_options`, `tax_default`, `tax_inclusive`, `business_name`, `business_address`, `business_vat_id`). Added `m002_tpos_fields` migration with 4 ALTER TABLE ADD COLUMN statements.

**T02 (8m):** Rewired the POST handler with: (1) TPoS detection via `get_installed_extension("tpos")`; (2) conditional `default_exts` list including "tpos" only when installed; (3) `merchant_credentials` URL construction from `settings.lnbits_baseurl`; (4) conditional httpx POST to `/tpos/api/v1/tposs` with merchant's adminkey; (5) try/except graceful degradation with warning field population. Updated `create_arrangement` in CRUD to accept and pass through new fields.

**T03 (15m):** Created 9 tests in 5 classes covering: TPoS happy path with httpx payload verification, TPoS-absent degradation with default_exts verification, httpx failure degradation, merchant credentials in both paths, and extended CreateArrangement field acceptance/defaults.

## Verification

- `pytest tests/extensions/orangepiller/ -v` → **29 passed** (20 M001 + 9 S01) in 0.60s
- All 3 risk retirements proven:
  - Cross-extension HTTP: httpx POST to TPoS API with correct URL, adminkey, and payload verified
  - Merchant credentials: `/wallet?usr={user_id}` surfaced in both TPoS-present and TPoS-absent paths
  - TPoS detection: `get_installed_extension` used for detection; graceful degradation on absent/failure
- POST handler has 3 code paths: (a) TPoS + success → full fields, (b) TPoS absent → warning, (c) TPoS + failure → warning
- All 20 M001 tests unchanged and passing — no regressions

## Requirements Advanced

- R101 (TPoS auto-provisioning) — POST handler creates TPoS terminal via httpx, stores tpos_id and tpos_url on arrangement
- R102 (Extended onboarding form) — CreateArrangement accepts merchant_name, currency, tip_options, tax_default, tax_inclusive, business_name, business_address, business_vat_id
- R103 (Graceful degradation) — Arrangement created with tpos_id=None and warning when TPoS absent or HTTP call fails
- R106 (Merchant credentials surfaced) — merchant_credentials contains `/wallet?usr={user_id}` login URL in API response

## Requirements Validated

- R101 — TPoS auto-provisioning proven by test_create_arrangement_with_tpos and test_httpx_called_with_tpos_payload
- R102 — Extended fields proven by test_extended_create_fields_accepted and test_extended_create_fields_defaults
- R103 — Graceful degradation proven by test_create_arrangement_without_tpos, test_default_exts_omits_tpos_when_not_installed, and test_create_arrangement_tpos_http_failure
- R106 — Merchant credentials proven by test_merchant_credentials_format_with_tpos and test_merchant_credentials_format_without_tpos

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

- T03 delivered 9 tests instead of the planned 5+ — added TPoS payload verification, default_exts verification, and field defaults test for finer coverage.

## Known Limitations

- TPoS integration is proven via mocked HTTP calls only — real runtime integration (actual TPoS terminal creation on a live instance) deferred to operational verification / UAT
- merchant_credentials is a simple `/wallet?usr={user_id}` URL — if LNbits auth model changes, this may need updating
- No validation that the TPoS terminal is actually functional after creation (URL accessibility check deferred to S02 UAT)

## Follow-ups

- S02 must consume `tpos_url` and `merchant_credentials` from arrangement responses to render QR codes and dashboard links
- Operational UAT should verify the full flow on a live LNbits instance with TPoS installed

## Files Created/Modified

- `orangepiller/models.py` — Added 5 fields to Arrangement (4 DB + 1 response-only), 8 fields to CreateArrangement
- `orangepiller/migrations.py` — Added m002_tpos_fields migration function
- `orangepiller/views_api.py` — Added TPoS detection, conditional httpx provisioning, credential construction, graceful degradation
- `orangepiller/crud.py` — Extended create_arrangement with tpos_id, tpos_url, merchant_name, merchant_credentials params
- `tests/extensions/orangepiller/test_tpos_onboarding.py` — 9 tests across 5 classes

## Forward Intelligence

### What the next slice should know
- `tpos_url` is populated only when TPoS is installed AND httpx succeeds — S02 templates must handle `null` gracefully and show an informative message instead of a broken QR code
- `merchant_credentials` is always populated (contains login URL regardless of TPoS status) — safe to always render
- `warning` field is response-only (`no_database=True`) — it's set on the POST response but NOT persisted; GET endpoints return arrangements without warning. If S02 needs to show "TPoS not provisioned" on the dashboard, it should check `tpos_id is null` rather than relying on the warning field.

### What's fragile
- The httpx call to `/tpos/api/v1/tposs` uses `settings.lnbits_baseurl` for the internal URL — if LNbits is behind a reverse proxy where the internal URL differs from the public URL, this may fail. The try/except ensures it degrades gracefully but worth noting for operational deployment.
- `get_installed_extension("tpos")` import path is `lnbits.core.crud.extensions` — if LNbits core refactors this, the import breaks.

### Authoritative diagnostics
- `pytest tests/extensions/orangepiller/test_tpos_onboarding.py -v` — 9 tests prove all three risk retirements; if any fail, the TPoS integration contract is broken
- POST response `warning` field — check this first when TPoS provisioning doesn't work; it contains the specific failure reason

### What assumptions changed
- Original plan assumed we'd need to discover what `create_user_account_no_ckeck` returns for auth — it returns a User object with `.id`, and we construct the login URL as `/wallet?usr={user.id}` which is the standard LNbits user-id auth pattern.
