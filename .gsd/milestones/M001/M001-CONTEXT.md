# M001: Orange Piller Extension — Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

## Project Description

Orange Piller is a standalone LNbits extension for grassroots Bitcoin merchant onboarding. A Bitcoin enthusiast ("orange piller") pays a local merchant cash, creates their LNbits account through the extension, and sets up an automated payback arrangement. A configurable percentage of the merchant's incoming Bitcoin payments is rerouted internally to the orange piller's wallet until the sat-denominated debt is fully repaid.

## Why This Milestone

This is the only milestone — it delivers the complete extension from zero to installable package. The core mechanic (payment rerouting with debt tracking) is proven by the existing splitpayments extension pattern, so the technical risk is manageable in a single milestone.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Open the Orange Piller extension, fill out a form, and create a merchant's LNbits account with a payback arrangement configured
- See incoming payments to the merchant automatically split — the configured percentage goes to the orange piller's wallet
- View a dashboard of all onboarded merchants with payback progress
- As a merchant, see the arrangement details and repayment progress from their own LNbits dashboard
- Adjust reroute percentage or forgive remaining debt on any active arrangement
- See the arrangement automatically complete when the debt reaches zero

### Entry point / environment

- Entry point: LNbits web UI → Orange Piller extension page
- Environment: LNbits instance (local dev or deployed)
- Live dependencies involved: LNbits core (account creation, payment system, invoice listeners)

## Completion Class

- Contract complete means: Extension scaffold passes lint, migrations run, API endpoints return correct responses, models serialize properly
- Integration complete means: Payment rerouting actually works — pay the merchant, see the split arrive in the orange piller's wallet, debt decremented correctly
- Operational complete means: Extension installs from GitHub manifest, survives LNbits restart, handles concurrent payments without overpayment

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- End-to-end: orange piller onboards merchant → merchant receives payment → percentage rerouted to orange piller → debt updated → debt reaches zero → rerouting stops
- Both dashboards show accurate, real-time arrangement state
- Extension installs cleanly on a fresh LNbits instance from the GitHub manifest

## Risks and Unknowns

- Concurrency in payment rerouting — two simultaneous payments could cause a race condition in debt tracking, potentially overpaying the orange piller. Must use database-level locking or atomic updates.
- Account creation permissions — the extension needs to call `create_user_account_no_ckeck` which is a core service. Need to verify the extension has access to this from its context (via LNbits core imports).
- Auto-enabling extension on new accounts — `default_exts` parameter handles this, but need to confirm the extension is registered/installed on the instance before it can be auto-enabled for a new user.

## Existing Codebase / Prior Art

- `/tmp/splitpayments/` — Reference extension that does permanent percentage-based payment splits. Almost identical payment interception pattern. Key files: `__init__.py`, `tasks.py`, `crud.py`, `models.py`, `views_api.py`, `views.py`, `migrations.py`
- `/tmp/example/` — Official LNbits example extension scaffold
- `lnbits/tasks.py` — `register_invoice_listener`, `wait_for_paid_invoices` pattern for hooking into payment events
- `lnbits/core/services/payments.py` — `create_invoice`, `pay_invoice` for internal transfers
- `lnbits/core/services/users.py` — `create_user_account_no_ckeck` with `default_exts` for account creation + auto-enabling extensions
- `lnbits/core/crud/extensions.py` — `create_user_extension` for programmatic extension activation
- `lnbits/core/models/extensions.py` — `Extension`, `UserExtension`, `InstallableExtension` models

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R001-R010 — All active requirements are owned by this milestone

## Scope

### In Scope

- Extension scaffold (repo structure, config.json, manifest.json)
- Merchant onboarding API + form (creates LNbits account, wallet, arrangement)
- Payment rerouting engine (invoice listener, internal transfer, debt decrement)
- Exact debt tracking with final payment cap
- Orange piller dashboard (multi-merchant, progress)
- Merchant transparency view
- Arrangement management (adjust %, forgive debt)
- Clean cutover when debt reaches zero
- Visual status change on repayment completion

### Out of Scope / Non-Goals

- Fiat-denominated debt tracking
- External Lightning address payback (LNURL/Lightning Address)
- Merchant dispute mechanism
- Bitcoin store map listing (deferred)
- Mobile app — this is a web UI extension only

## Technical Constraints

- Pydantic v1 (1.10.x) — LNbits has not migrated to v2
- SQLAlchemy 1.4 — async, but not 2.0 style
- No new Python dependencies — LNbits policy is to use existing deps from pyproject.toml
- Extension must work with both SQLite and PostgreSQL
- Frontend uses Quasar/Vue.js via Jinja2 templates — no build step, no npm in the extension itself
- Extension code identifier must be lowercase alphanumeric, no dashes: `orangepiller`

## Integration Points

- LNbits core payment system — invoice listener for intercepting incoming payments
- LNbits core user system — programmatic account/wallet creation
- LNbits core extension system — auto-enabling extension on new accounts
- LNbits UI framework — Quasar components, base.html template inheritance

## Open Questions

- Whether to show the merchant's LNbits login credentials to the orange piller after account creation, or generate a one-time login link — needs to follow whatever pattern LNbits uses for account access
- Whether LNbits has a built-in notification system extensions can hook into, or if "notification" just means visual status in the UI
