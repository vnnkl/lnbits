# S01 Post-Slice Assessment

**Verdict: Roadmap unchanged.**

## Success Criteria Coverage

All 7 success criteria have at least one remaining owning slice (S02) or are already proven by S01. No blocking gaps.

- Extended onboarding → ✅ S01
- TPoS URL in arrangement → ✅ S01
- Dashboards show TPoS links with QR codes → S02
- Printable poster with QR → S02
- Merchant credentials surfaced → ✅ S01 (API); S02 (display)
- Graceful degradation without TPoS → ✅ S01
- M001 regression-free → ✅ S01 (29/29 pass); S02 must maintain

## Boundary Map

S01 produced exactly what the boundary map specified. No contract drift:
- `Arrangement` extended with `tpos_id`, `tpos_url`, `merchant_name`, `merchant_credentials` (4 DB fields + 1 response-only `warning`)
- `CreateArrangement` extended with 8 merchant/TPoS config fields
- GET and POST endpoints return all new fields
- `m002_tpos_fields` migration in place

S02 consumes these fields unchanged.

## Requirement Coverage

- R104 (TPoS link + QR on dashboards) — active, owned by S02
- R105 (Printable poster) — active, owned by S02
- No requirements invalidated, re-scoped, or newly surfaced by S01

## Risk Retirements

All 3 S01 risks fully retired:
- Cross-extension HTTP call mechanics → proven via httpx POST with correct URL/auth/payload
- Merchant credentials → `/wallet?usr={user_id}` pattern discovered and implemented
- TPoS installation detection → `get_installed_extension` with graceful degradation on 3 code paths

No new risks emerged that affect S02 (low-risk frontend slice).

## Forward Notes for S02

From S01 forward intelligence:
- `tpos_url` can be null — templates must handle gracefully (show message, not broken QR)
- `merchant_credentials` always populated — safe to always render
- `warning` is response-only (`no_database=True`) — S02 should check `tpos_id is null` for "not provisioned" state, not rely on warning field from GET responses
