# Decisions Register

<!-- Append-only. Never edit or remove existing rows.
     To reverse a decision, add a new row that supersedes it.
     Read this file at the start of any planning or research phase. -->

| # | When | Scope | Decision | Choice | Rationale | Revisable? |
|---|------|-------|----------|--------|-----------|------------|
| 1 | 2026-03-16 | M001/S01 | Extension code identifier | `orangepiller` (lowercase, no dashes) | LNbits convention for extension IDs — used in DB schema prefix, router prefix, static file paths, and `default_exts` parameter | No |
| 2 | 2026-03-16 | M001/S01 | CRUD update pattern | `update_arrangement` accepts `**kwargs` for flexible field updates | Allows T02/S04 to update any combination of fields without creating separate update functions per field | Yes |
| 3 | 2026-03-16 | M001/S01 | Pydantic v1 computed properties | `@property` for `remaining_debt`, `progress_percent`, `is_completed` | Pydantic v1 doesn't support `@computed_field`; properties work but aren't included in `.dict()` serialization — API responses must add them explicitly if needed | Yes |
| 4 | 2026-03-16 | M001/S02 | Atomic debt update strategy | SQL UPDATE with CASE cap + SELECT within `db.connect()` context | Avoids read-then-update race for concurrent payments; avoids `RETURNING` clause for SQLite < 3.35 portability | No |
| 5 | 2026-03-16 | M001/S02 | Debt update before transfer | Update debt first, rollback if `pay_invoice` fails | Prevents concurrent payments from both reading the same remaining_debt; rollback handles transfer failure safely | Yes |
| 6 | 2026-03-16 | M001/S03 | Computed fields in JS not API | `remaining_debt` and `progress_percent` computed client-side from `total_debt_sats` and `repaid_sats` | Pydantic v1 `@property` fields aren't included in `.dict()` serialization; computing in JS avoids touching model serialization | No |
| 7 | 2026-03-16 | M001/S04 | Single UpdateArrangement model for PUT | `UpdateArrangement` with `reroute_percent: Optional[int]` and `forgive: Optional[bool]` — one endpoint handles both operations | Cleaner than separate endpoints; `update_arrangement(**kwargs)` CRUD already supports flexible updates | No |
| 8 | 2026-03-16 | M001/S05 | Extension packaging follows splitpayments pattern | config.json fields, file layout, min_lnbits_version=1.3.0 | Proven convention from existing LNbits extensions; 1.3.0 covers all APIs used | No |
| 9 | 2026-03-16 | M001/S05 | Transition-aware toast notifications | Compare old vs new arrangement arrays by id; fire toast only on actual status transition | Prevents false notifications on initial page load or refresh without changes | Yes |
| 10 | 2026-03-16 | M002 | TPoS as soft dependency via HTTP | Internal `httpx` call to TPoS API, not direct Python imports | Keeps orangepiller installable without TPoS; graceful degradation if TPoS absent | No |
| 11 | 2026-03-16 | M002 | Core TPoS settings only in onboarding form | Name, currency, tips, tax, business info | Power-user features (inventory, ATM, Stripe) deferred to merchant self-service | No |
| 12 | 2026-03-16 | M002 | TPoS conditionally added to default_exts | Only include "tpos" in `default_exts` when TPoS is detected as installed | Prevents account creation failure if TPoS not installed | No |
| 13 | 2026-03-16 | M002/S01 | warning field uses no_database=True | `Field(None, no_database=True)` for response-only warning on Arrangement | Matches LNbits core pattern (wallets.py, users.py); warning is transient provisioning status, not persisted state | No |
| 14 | 2026-03-16 | M002/S01 | Merchant credentials as login URL | `merchant_credentials = f"{base_url}/wallet?usr={user.id}"` | Standard LNbits user-id auth; `create_user_account_no_ckeck` returns User with `.id` — simplest shareable credential | Yes |
| 15 | 2026-03-16 | M002/S01 | try/except around cross-extension httpx | httpx failure sets tpos_id=None + warning, never blocks arrangement creation | Arrangement is the primary deliverable; TPoS is a soft enhancement that must not prevent onboarding | No |
| 16 | 2026-03-16 | M002/S02 | QR dialog shared across both tables | Single showQrDialog + qrDialogUrl state, one showQr() method | Avoids duplicating dialog markup and state; both tables call the same method | Yes |
| 17 | 2026-03-16 | M002/S02 | Poster route is unauthenticated | No check_user_exists dependency on GET /poster/{id} | Poster URL is intended to be shared publicly — anyone with the URL should see the QR code; arrangement_id is the implicit auth token | No |
| 18 | 2026-03-16 | M002/S02 | {% raw %} blocks for Vue in Jinja | All {{ }} Vue interpolation wrapped in {% raw %}{% endraw %} | Jinja silently eats Vue template expressions without this; same pattern used in index.html and poster.html | No |
| 19 | 2026-03-16 | M002/S02 | Explicit lnbits-qrcode registration on poster | window.app.component('lnbits-qrcode', ...) on poster page | Poster doesn't use LNbits.common.VueApp which auto-registers components; manual registration required | No |
