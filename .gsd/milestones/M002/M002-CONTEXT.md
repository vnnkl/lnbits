# M002: Merchant Activation Kit — Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

## Project Description

M002 extends the orangepiller extension to auto-provision a TPoS (point of sale) terminal during merchant onboarding, surface shareable payment links with QR codes on both dashboards, and generate a printable merchant poster for the counter. This closes the gap between "account created" and "merchant accepting Bitcoin" — the orange piller walks out with a poster to print and a link to text.

## Why This Milestone

M001 built the complete rerouting engine, but the merchant has no practical way to accept payments. The TPoS extension already provides a shareable, public-facing payment terminal (customer enters amount, gets Lightning invoice) — but it has to be manually set up. M002 automates that setup during onboarding and delivers the activation artifacts (links, QR, poster) the orange piller needs to make the merchant operational immediately.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Fill the extended onboarding form (including merchant name, currency, tip/tax settings, business info) and create a merchant with a ready-to-use TPoS terminal in one click
- Copy the TPoS shareable URL or scan its QR code from the dashboard
- Open a printable poster page with the merchant's name and a QR code pointing to the TPoS terminal — print it and put it by the register
- See the TPoS link on the merchant's own dashboard
- Get the merchant's LNbits login credentials to share with them
- Still onboard merchants normally if TPoS is not installed on the instance (graceful degradation with warning)

### Entry point / environment

- Entry point: LNbits web UI → Orange Piller extension page (extended onboarding form)
- Environment: LNbits instance (local dev or deployed)
- Live dependencies involved: LNbits core (account creation, payment system), TPoS extension (soft dependency — must be installed for TPoS provisioning, but onboarding works without it)

## Completion Class

- Contract complete means: POST endpoint creates TPoS via internal HTTP call, arrangement stores TPoS URL, migration adds new columns, tests verify TPoS provisioning and graceful degradation
- Integration complete means: TPoS terminal is actually accessible at the returned URL and generates Lightning invoices for the merchant's wallet; payments through TPoS trigger the rerouting engine
- Operational complete means: Full flow works end-to-end: onboard → TPoS created → customer pays via TPoS → rerouting triggers → debt decremented

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- Extended onboarding creates account + wallet + TPoS + arrangement atomically, returning all relevant URLs
- The TPoS page at the returned URL is functional — a customer can enter an amount and get a Lightning invoice
- Payments received through the TPoS trigger the rerouting engine (debt decremented, split transferred)
- Dashboards show TPoS links with QR codes on both orange piller and merchant views
- Printable poster renders correctly with merchant name and QR code
- Onboarding succeeds with a warning when TPoS is not installed

## Risks and Unknowns

- Cross-extension API call mechanics — calling TPoS's API from orangepiller requires an internal HTTP call with the merchant's adminkey. Need to construct the correct base URL for the internal call (localhost vs reverse proxy).
- TPoS `default_exts` — TPoS must be in the `default_exts` list during account creation so it's enabled on the merchant's account. But TPoS might not be installed, so this must be conditional.
- Merchant credentials — `create_user_account_no_ckeck` returns a User object, but it's unclear what authentication credentials (if any) are generated. Need to research whether there's a login link, username/password, or auth token to share with the merchant.
- Internal HTTP call URL — extensions don't have direct access to "what's my own base URL." The TPoS API call needs a valid URL. The `Request` object in FastAPI handlers has `request.base_url`, which should work.

## Existing Codebase / Prior Art

- `orangepiller/views_api.py` — Current POST handler that calls `create_user_account_no_ckeck`. This is where TPoS provisioning will be added.
- `orangepiller/models.py` — `Arrangement` and `CreateArrangement` models. Need new fields for TPoS data and merchant settings.
- `orangepiller/migrations.py` — Has `m001_initial`. Will need `m002_tpos_fields` migration.
- `orangepiller/templates/orangepiller/index.html` — Dashboard template. Needs TPoS link, QR, and poster link columns.
- `orangepiller/static/js/index.js` — Vue app. Needs extended form fields and QR rendering.
- TPoS extension source: https://github.com/lnbits/tpos — `POST /tpos/api/v1/tposs` with `CreateTposData` model creates a terminal. Public view at `/tpos/{tpos_id}`. Auth via admin key header.
- TPoS `CreateTposData` relevant fields: `wallet`, `name`, `currency`, `tax_inclusive`, `tax_default`, `tip_options`, `business_name`, `business_address`, `business_vat_id`.
- LNbits `Wallet` model has `.adminkey` and `.inkey` — available from `user.wallets[0]` after account creation.

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R101 — TPoS auto-provisioning (primary M002 capability)
- R102 — Extended onboarding form with TPoS settings
- R103 — Graceful degradation without TPoS
- R104 — TPoS link and QR on dashboards
- R105 — Printable merchant poster
- R106 — Merchant login credentials

## Scope

### In Scope

- Extended onboarding API with TPoS config fields
- Internal HTTP POST to TPoS API during onboarding
- Conditional TPoS in `default_exts` (only when TPoS is installed)
- DB migration adding TPoS-related columns to arrangements
- TPoS URL and QR code on both dashboards
- Printable poster HTML route
- Merchant credentials surfacing (whatever is available from `create_user_account_no_ckeck`)
- Extended onboarding form UI with TPoS settings
- Graceful degradation when TPoS not installed

### Out of Scope / Non-Goals

- Full TPoS configuration (inventory, ATM/withdraw, Stripe, receipt printing, remote mode)
- Direct TPoS code imports (use HTTP API only for soft dependency)
- Modifying the TPoS extension itself
- Mobile-optimized poster layout (print-optimized is sufficient)
- LndHub or other extension auto-provisioning (TPoS only for M002)

## Technical Constraints

- Pydantic v1 (1.10.x) — LNbits has not migrated to v2
- SQLAlchemy 1.4 — async
- No new Python dependencies
- Extension must work with both SQLite and PostgreSQL
- Frontend uses Quasar/Vue.js via Jinja2 templates
- TPoS is a soft dependency — orangepiller must not import TPoS code directly
- Internal HTTP calls must use `httpx` (already in LNbits deps) with the request's base URL

## Integration Points

- TPoS extension API — `POST /tpos/api/v1/tposs` to create terminals
- TPoS public view — `/tpos/{tpos_id}` is the shareable payment page
- LNbits core user system — `create_user_account_no_ckeck` for account creation with `default_exts`
- LNbits Wallet model — `.adminkey` for authenticating TPoS API calls on behalf of the merchant

## Open Questions

- What does `create_user_account_no_ckeck` return for auth credentials? Need to check if the User model includes a password, auth token, or login URL that can be shared with the merchant.
- Best way to construct the internal base URL for TPoS API calls — `request.base_url` from FastAPI, or `settings.lnbits_baseurl`, or localhost with the known port?
- Whether to detect TPoS installation by attempting the API call and catching the 404, or by checking the extension registry directly.
