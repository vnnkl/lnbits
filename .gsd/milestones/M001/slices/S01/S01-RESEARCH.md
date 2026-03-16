# S01 — Extension Scaffold + Onboarding API — Research

**Date:** 2026-03-16

## Summary

S01 owns R001 (merchant onboarding) and R002 (payback arrangement configuration), and supports R009 (standalone extension packaging). The LNbits codebase provides clear, proven patterns for all three. The `example` and `splitpayments` extensions at `/tmp/example/` and `/tmp/splitpayments/` are near-perfect templates — the extension scaffold is a mechanical copy-and-rename. The critical piece is the onboarding API endpoint that atomically creates a merchant account + wallet + arrangement.

The `create_user_account_no_ckeck` function in `lnbits/core/services/users.py` does exactly what we need: it accepts `default_exts: list[str]` to auto-enable extensions on the new account, creates the account and wallet in a single DB transaction, and returns a `User` object that includes the wallet list (with `id`, `adminkey`, `inkey`). This retires two key risks from the roadmap: account creation from extension context, and auto-enable on new accounts.

The main implementation decision is the `Arrangement` model and DB schema, which must satisfy the boundary contracts to S02 (payment rerouting needs `get_arrangement_by_merchant_wallet`, `update_arrangement_repaid`), S03 (dashboard needs `get_arrangements_by_piller`), and S04 (management needs `update_arrangement`). The schema is straightforward — single table, no joins needed.

## Recommendation

Follow the splitpayments extension structure exactly. Copy the scaffold from `/tmp/example/`, rename to `orangepiller`, and build out:

1. **Scaffold**: `__init__.py`, `config.json`, `manifest.json`, `pyproject.toml`, `views.py`, `crud.py`, `models.py`, `migrations.py`, `views_api.py`, `tasks.py` (stub for S02), `templates/orangepiller/index.html` (stub for S03)
2. **Models**: `Arrangement` (Pydantic BaseModel), `CreateArrangement` (request model)
3. **Migration**: `m001_initial` creating `orangepiller.arrangements` table
4. **CRUD**: All functions specified in the boundary map
5. **API**: `POST /api/v1/arrangements` (onboard merchant), `GET /api/v1/arrangements` (list), `PUT /api/v1/arrangements/{id}` (update — stub body for S04)
6. **Onboarding logic**: Call `create_user_account_no_ckeck(default_exts=["orangepiller"])`, then create the arrangement record linking the new merchant wallet to the orange piller's wallet

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Account + wallet creation | `create_user_account_no_ckeck()` from `lnbits.core.services.users` | Handles account, wallet, and extension activation atomically in one DB transaction. Returns `User` with populated `wallets` list |
| Extension auto-enable | `default_exts` parameter on `create_user_account_no_ckeck` | Creates `UserExtension` records for each ext ID — proven pattern |
| Unique IDs | `urlsafe_short_hash()` from `lnbits.helpers` | LNbits convention for all entity IDs (uses shortuuid) |
| DB access layer | `Database("ext_orangepiller")` from `lnbits.db` | Provides `insert`, `fetchall`, `fetchone`, `execute` with schema-qualified table names (`orangepiller.arrangements`) |
| Auth decorators | `require_admin_key`, `check_user_exists` from `lnbits.decorators` | Standard auth for API endpoints. `require_admin_key` returns `WalletTypeInfo` with `wallet.id` |
| Template rendering | `template_renderer(["orangepiller/templates"])` | Jinja2 with Quasar/Vue base template inheritance |

## Existing Code and Patterns

- `/tmp/example/__init__.py` — Canonical extension entry point. Router prefix, static files, start/stop lifecycle, `__all__` exports. Copy and rename.
- `/tmp/example/config.json` — Extension metadata (name, description, tile image, contributors). Simple JSON — adapt for orangepiller.
- `/tmp/splitpayments/crud.py` — Shows `Database("ext_splitpayments")` pattern, `fetchall` with model class, `insert` with model instance. Our CRUD will be more complex but same patterns.
- `/tmp/splitpayments/views_api.py` — Shows `Depends(require_admin_key)` pattern returning `WalletTypeInfo`. Use `wallet.wallet.id` to identify the calling user's wallet.
- `/tmp/splitpayments/migrations.py` — Shows migration function naming (`m001_initial`), schema-qualified tables (`splitpayments.targets`), `db.timestamp_now` for timestamps. Use `Connection` type hint.
- `/tmp/splitpayments/tasks.py` — Shows `register_invoice_listener` + `asyncio.Queue` pattern. S01 only needs a stub; S02 fills in the real logic.
- `lnbits/core/services/users.py` lines 43-83 — `create_user_account_no_ckeck` full implementation. Takes `Account | None`, `wallet_name`, `default_exts`, `conn`. Returns `User` with wallets populated. Key: `account.id` is set to `uuid4().hex` if not provided.
- `lnbits/core/crud/wallets.py` — `create_wallet` returns `Wallet` with `id`, `adminkey`, `inkey`. The `User.wallets` list contains these after `get_user_from_account`.
- `/tmp/splitpayments/views.py` — Shows `template_renderer` pattern. Note: example extension uses `request` as first arg to `TemplateResponse` while splitpayments uses the old-style kwargs — use the example's newer pattern.
- `/tmp/example/models.py` — Shows simple Pydantic v1 models (no `model_config`, uses `class Config` if needed).

## Constraints

- **Pydantic v1 (1.10.26)** — No `model_validator`, no `model_config`. Use `@validator`, `class Config`, `.dict()` not `.model_dump()`.
- **LNbits 1.5.1-rc1** — The `create_user_account_no_ckeck` signature includes `default_exts` parameter (confirmed in source).
- **No new Python dependencies** — Everything needed is already in LNbits core.
- **Schema-qualified tables** — All tables must be prefixed: `orangepiller.arrangements`, not just `arrangements`.
- **Extension code identifier** — Must be `orangepiller` (lowercase, no dashes — D005).
- **DB compatibility** — Must work with both SQLite and PostgreSQL. Use `db.timestamp_now` for default timestamps, TEXT for IDs.
- **`Account` model** — Has `validate_fields()` method called during creation. If passing username/email, uniqueness is enforced. For merchant accounts created by the extension, we can create with just an ID (no username/email required).
- **`User` return type** — `create_user_account_no_ckeck` returns `User` which has `wallets: list[Wallet]`. The first wallet's `id` is what we store as `merchant_wallet` in the arrangement.

## Common Pitfalls

- **Template renderer path** — The splitpayments extension passes `["splitpayments/templates"]` but the template file is at `templates/splitpayments/index.html`. The renderer resolves relative to the extensions directory. Follow the exact same nesting pattern.
- **views.py TemplateResponse signature** — The example extension uses the newer `TemplateResponse(request, "example/index.html", {...})` pattern while splitpayments uses the older `TemplateResponse("splitpayments/index.html", {"request": request, ...})`. Use the newer pattern from example.
- **`WalletTypeInfo` is a dataclass, not Pydantic** — Access via `wallet.wallet.id` (the first `wallet` is the dependency injection name, `.wallet` is the `Wallet` attribute, `.id` is the wallet ID).
- **Account with no credentials** — When creating a merchant account with no username/password, the merchant has no way to log in except via the user ID URL (`/wallet?usr=<user_id>`). This is actually fine for our use case — the orange piller gets the user ID and can share it with the merchant. But this is an open question flagged in M001-CONTEXT.
- **Migration connection type** — Migration functions take `db: Connection`, not `db: Database`. The parameter name is `db` by convention but it's actually a `Connection` instance.
- **`db.timestamp_now`** — Returns a SQL expression string, not a Python value. Use it in CREATE TABLE DDL for DEFAULT clauses, not in Python code.

## Open Risks

- **Merchant credential sharing** — After `create_user_account_no_ckeck`, the merchant can only access their account via `?usr=<user_id>`. There's no built-in "invitation link" or one-time login mechanism. The API response should include the user ID so the orange piller can share it. This is a UX question, not a blocker — S01 just returns the data, S03/S04 handle the UX.
- **Extension not installed on instance** — `default_exts=["orangepiller"]` will silently fail if the orangepiller extension isn't installed on the LNbits instance (the `try/except` in `create_user_account_no_ckeck` catches and logs the error). The extension will be installed if the orange piller is using it, but we should verify this works correctly.
- **Concurrent arrangement creation** — Two orange pillers onboarding the same merchant email/username simultaneously could race. Low probability since merchant accounts are created with just an ID (no username), but if we add username support later, it needs `UNIQUE` constraints.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| LNbits | (searched "lnbits") | none found |

No relevant professional agent skills exist for LNbits extension development. The reference extensions (`/tmp/example/`, `/tmp/splitpayments/`) serve as the authoritative patterns.

## Sources

- `create_user_account_no_ckeck` signature and behavior (source: `lnbits/core/services/users.py` lines 43-83)
- Extension scaffold pattern (source: `/tmp/example/__init__.py`, `config.json`, `manifest.json`)
- Payment split and CRUD patterns (source: `/tmp/splitpayments/crud.py`, `views_api.py`, `migrations.py`)
- Database and helper APIs (source: `lnbits/db.py`, `lnbits/helpers.py`)
- Auth decorators (source: `lnbits/decorators.py`)
- Wallet model with adminkey/inkey (source: `lnbits/core/models/wallets.py`, `lnbits/core/crud/wallets.py`)
