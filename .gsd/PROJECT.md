# Orange Piller — LNbits Extension

## What This Is

A standalone LNbits extension that enables Bitcoin enthusiasts ("orange pillers") to onboard local merchants into accepting Bitcoin. The orange piller pays the merchant cash upfront, creates their LNbits account, and sets up an automated payback arrangement where a configurable percentage of the merchant's incoming Bitcoin payments is rerouted to the orange piller until the sat-denominated debt is repaid.

## Core Value

The payment rerouting engine — intercepting incoming payments and splitting them according to the payback arrangement, with exact debt tracking and automatic cutover when the debt reaches zero.

## Current State

S01 (Extension scaffold + onboarding API) is complete. S02 (Payment rerouting engine) is complete — atomic debt tracking, internal transfers with rollback, 11 passing tests. S03 (Orange piller dashboard) is complete — Quasar table with progress bars, status badges, computed fields. S04 (Merchant view + arrangement management) is complete — merchant transparency view, edit/forgive management controls with authorized PUT endpoint. S05 (Clean cutover, notifications & packaging) is complete — cutover tests pass, toast notifications on both dashboards, extension packaging with config.json/tile/README/LICENSE. All 5 slices complete. Milestone M001 ready for UAT.

## Architecture / Key Patterns

- Standalone extension repo (not inside lnbits core)
- Python/FastAPI backend following LNbits extension conventions: `__init__.py`, `views.py`, `views_api.py`, `crud.py`, `models.py`, `tasks.py`, `migrations.py`
- Quasar/Vue.js frontend templates (LNbits standard)
- Payment interception via `register_invoice_listener` + `asyncio.Queue`
- Internal wallet-to-wallet transfers via `create_invoice` + `pay_invoice`
- Merchant account creation via `create_user_account_no_ckeck` with `default_exts=["orangepiller"]`
- Pydantic v1 models, SQLAlchemy 1.4, async Python

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [ ] M001: Orange Piller Extension — Full extension from scaffold to installable package with onboarding, payment rerouting, dashboards, and arrangement management
