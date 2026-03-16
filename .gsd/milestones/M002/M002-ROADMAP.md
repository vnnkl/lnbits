# M002: Merchant Activation Kit

**Vision:** Extend the onboarding flow to auto-provision a TPoS payment terminal for the merchant, surface shareable payment links with QR codes on both dashboards, and generate a printable poster — so the orange piller walks out with everything needed to make the merchant operational immediately.

## Success Criteria

- Orange piller fills the extended onboarding form (with merchant name, currency, tip/tax settings) → merchant account created with TPoS terminal auto-provisioned
- The TPoS URL returned in the arrangement is accessible and generates Lightning invoices
- Both dashboards show TPoS links with QR codes
- A printable poster page renders with merchant name and QR code at a dedicated URL
- Merchant's LNbits login credentials (or login link) are surfaced to the orange piller
- Onboarding works without TPoS installed — arrangement created with warning, no TPoS URL
- Existing M001 functionality (rerouting, debt tracking, management, cutover) continues to work

## Key Risks / Unknowns

- Cross-extension HTTP call mechanics — constructing the correct internal URL and handling auth for TPoS API calls from within orangepiller
- Merchant credentials — unclear what `create_user_account_no_ckeck` returns for authentication; need to discover what's shareable
- TPoS installation detection — need a reliable way to check if TPoS is installed before attempting API calls

## Proof Strategy

- Cross-extension HTTP call → retire in S01 by proving `POST /tpos/api/v1/tposs` succeeds from within the orangepiller POST handler and returns a valid TPoS ID
- Merchant credentials → retire in S01 by inspecting the User object returned from `create_user_account_no_ckeck` and surfacing whatever auth info is available
- TPoS installation detection → retire in S01 by implementing detection (try-call or registry check) and proving graceful degradation

## Verification Classes

- Contract verification: Python tests, API response checks, migration verification, model field validation
- Integration verification: TPoS terminal accessible at returned URL, payments through TPoS trigger rerouting engine
- Operational verification: Full onboarding-to-payment flow on running LNbits instance
- UAT / human verification: Poster print quality, dashboard QR scannability, onboarding UX

## Milestone Definition of Done

This milestone is complete only when all are true:

- All slices complete with passing verification
- Extended onboarding creates account + wallet + TPoS + arrangement atomically
- TPoS URL is functional — customer can pay at the returned URL
- Both dashboards show TPoS links with scannable QR codes
- Printable poster renders at a dedicated route with merchant name and QR
- Graceful degradation proven: onboarding without TPoS installed works with warning
- Merchant credentials surfaced in API response and visible on dashboard
- All M001 tests still pass (no regressions)

## Requirement Coverage

- Covers: R101, R102, R103, R104, R105, R106
- Partially covers: none
- Leaves for later: R011 (store map listing)
- Orphan risks: none

## Slices

- [ ] **S01: TPoS integration + extended onboarding** `risk:high` `depends:[]`
  > After this: Orange piller calls the extended POST endpoint with merchant name, currency, and TPoS settings → merchant account created with TPoS terminal auto-provisioned. API returns arrangement with TPoS URL and merchant credentials. Works without TPoS installed (arrangement created, TPoS fields null, warning in response). Verified via API calls and TPoS URL accessibility.

- [ ] **S02: Dashboards, QR codes & printable poster** `risk:low` `depends:[S01]`
  > After this: Orange piller dashboard shows TPoS link with QR code per arrangement, plus a "Print poster" button. Merchant dashboard shows their TPoS link. Poster route renders a print-optimized page with merchant name and QR. Verified by inspecting template output and QR rendering.

## Boundary Map

### S01 → S02

Produces:
- `models.py` → `Arrangement` model extended with `tpos_id: Optional[str]`, `tpos_url: Optional[str]`, `merchant_name: Optional[str]`, `merchant_credentials: Optional[str]`
- `models.py` → `CreateArrangement` extended with `merchant_name`, `currency`, `tip_options`, `tax_default`, `tax_inclusive`, `business_name`, `business_address`, `business_vat_id`
- `crud.py` → existing CRUD functions work with new fields (no new CRUD functions needed)
- `views_api.py` → `POST /api/v1/arrangements` returns arrangement with `tpos_id`, `tpos_url`, `merchant_name`, `merchant_credentials` populated
- `views_api.py` → `GET /api/v1/arrangements` and `GET /api/v1/merchant/arrangements` return arrangements with new fields
- `migrations.py` → `m002_tpos_fields` adding new columns to `orangepiller.arrangements`

Consumes:
- nothing from M002 (builds on M001 foundation)

### S01 → (external)

Consumes from TPoS extension (soft dependency via HTTP):
- `POST /tpos/api/v1/tposs` with `CreateTposData` — creates a TPoS terminal, returns `Tpos` with `id`
- `/tpos/{tpos_id}` — public URL pattern for the shareable payment page
