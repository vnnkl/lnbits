---
id: T01
parent: S04
milestone: M001
provides:
  - Merchant GET endpoint returning arrangements by merchant_wallet
  - Real PUT endpoint with auth, validation, forgiveness, percent update
  - UpdateArrangement Pydantic model
key_files:
  - orangepiller/views_api.py
  - orangepiller/models.py
  - tests/extensions/orangepiller/test_merchant_api.py
key_decisions:
  - PUT checks orange_piller_wallet ownership (not merchant_wallet) for authorization
  - Forgiveness and percent change are mutually exclusive in a single request (forgive takes priority)
patterns_established:
  - Merchant endpoint under /api/v1/merchant/ namespace to separate from piller endpoints
observability_surfaces:
  - loguru INFO "Arrangement updated" with arrangement_id and action type (forgive/percent_change)
  - HTTP 403 for unauthorized PUT, HTTP 400 for invalid updates
duration: 15m
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T01: Implement merchant GET and arrangement PUT endpoints

**Added merchant GET endpoint, real PUT with auth/validation/forgiveness/percent update, UpdateArrangement model, and 6 unit tests**

## What Happened

Added `UpdateArrangement` model to `models.py` with optional `reroute_percent` and `forgive` fields. Implemented `GET /api/v1/merchant/arrangements` that filters by `merchant_wallet == key_info.wallet.id` and wraps the single CRUD result in a list. Replaced the PUT 501 stub with a real handler that: fetches the arrangement (404 if missing), checks `orange_piller_wallet` ownership (403), handles forgiveness by setting `repaid_sats=total_debt_sats` and `status="completed"`, handles percent updates with 1–100 validation, and rejects modifications on completed arrangements (400). Added structured loguru INFO logging for both update actions. Wrote 6 unit tests covering all paths.

## Verification

- `pytest tests/extensions/orangepiller/test_merchant_api.py -v` — 6/6 passed
- `from orangepiller.models import UpdateArrangement` — imports cleanly
- Route inspection: `orangepiller_ext_api` has 4 routes (POST, GET /arrangements, GET /merchant/arrangements, PUT)

### Slice-level verification (partial — T01 is intermediate):
- ✅ `pytest tests/extensions/orangepiller/test_merchant_api.py -v` — all tests pass
- ✅ Code inspection: PUT checks `key_info.wallet.id == arrangement.orange_piller_wallet`
- ✅ Code inspection: merchant GET filters by `merchant_wallet`, not `orange_piller_wallet`
- ⏳ Code inspection: index.html has conditional merchant section — T02
- ⏳ Code inspection: index.js has management methods — T02

## Diagnostics

- Grep logs for `"Arrangement updated"` to see forgiveness and percent change events
- HTTP 403 returned for unauthorized PUT attempts (wallet mismatch)
- HTTP 400 returned for: completed arrangement updates, bad percent values (0, 101, negative), no update fields provided

## Deviations

- Added a "no update fields provided" 400 response when neither `forgive` nor `reroute_percent` is set — not in plan but necessary for completeness

## Known Issues

None

## Files Created/Modified

- `orangepiller/models.py` — Added `UpdateArrangement` model with optional `reroute_percent` and `forgive` fields
- `orangepiller/views_api.py` — Added merchant GET endpoint, replaced PUT stub with real implementation including auth, validation, logging
- `tests/extensions/orangepiller/test_merchant_api.py` — Created 6 unit tests for merchant GET and PUT endpoints
