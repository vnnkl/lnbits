# Orange Piller — LNbits Extension

## What This Is

A standalone LNbits extension that enables Bitcoin enthusiasts ("orange pillers") to onboard local merchants into accepting Bitcoin. The orange piller pays the merchant cash upfront, creates their LNbits account, and sets up an automated payback arrangement where a configurable percentage of the merchant's incoming Bitcoin payments is rerouted to the orange piller until the sat-denominated debt is repaid.

## Core Value

The payment rerouting engine — intercepting incoming payments and splitting them according to the payback arrangement, with exact debt tracking and automatic cutover when the debt reaches zero.

## Current State

**Milestone M001 (Orange Piller Extension) is complete.** All 5 slices delivered. All 10 requirements validated. 20/20 tests pass. Extension is structurally complete with full packaging for GitHub installation.

**What's built:**
- Atomic merchant onboarding (account + wallet + arrangement in one API call)
- Payment rerouting engine with concurrency-safe debt tracking and rollback
- Orange piller dashboard with progress bars, status badges, and management controls
- Merchant transparency view with arrangement details
- Arrangement management (adjust reroute %, forgive debt)
- Clean cutover (debt → zero → completed → rerouting stops)
- Toast notifications on both dashboards for completion transitions
- Extension packaging (config.json, manifest.json, tile, README, LICENSE)

**M002 (Merchant Activation Kit) is in planning.** Auto-provision TPoS terminals during onboarding, surface shareable payment links and QR codes on dashboards, generate printable merchant posters.

**What's pending:**
- Runtime UAT on a live LNbits instance (end-to-end payment flow, install from GitHub)
- Replace placeholder tile image with branded artwork

## Architecture / Key Patterns

- Standalone extension repo (not inside lnbits core)
- Python/FastAPI backend following LNbits extension conventions: `__init__.py`, `views.py`, `views_api.py`, `crud.py`, `models.py`, `tasks.py`, `migrations.py`
- Quasar/Vue.js frontend templates (LNbits standard)
- Payment interception via `register_invoice_listener` + `asyncio.Queue`
- Internal wallet-to-wallet transfers via `create_invoice` + `pay_invoice`
- Merchant account creation via `create_user_account_no_ckeck` with `default_exts=["orangepiller"]`
- Atomic SQL UPDATE with CASE for concurrent-safe debt capping
- Cross-extension integration via internal HTTP calls (not direct imports) for soft dependencies
- Pydantic v1 models, SQLAlchemy 1.4, async Python

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [x] M001: Orange Piller Extension — Full extension from scaffold to installable package with onboarding, payment rerouting, dashboards, and arrangement management. All 10 requirements validated. 20 tests pass.
- [ ] M002: Merchant Activation Kit — Auto-provision TPoS terminal during onboarding, shareable payment links with QR codes on dashboards, printable merchant poster for the counter.
