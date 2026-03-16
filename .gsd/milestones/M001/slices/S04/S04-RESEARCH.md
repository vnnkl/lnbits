# M001/S04 — Research

**Date:** 2026-03-16

## Summary

S04 delivers two capabilities: **R006 (Merchant transparency view)** — the merchant sees their payback arrangement from their own LNbits dashboard — and **R007 (Arrangement management)** — the orange piller can adjust reroute percentage and forgive remaining debt.

The extension scaffold (S01) and dashboard (S03) provide almost everything needed. The main work is: (1) a new merchant-facing API endpoint (`GET /api/v1/merchant/arrangements`) that returns arrangements where the authenticated wallet is the *merchant_wallet*, (2) replacing the PUT stub with real update logic including input validation and authorization, and (3) extending the existing `index.html` template + `index.js` to conditionally show a merchant view section when the user has merchant arrangements, plus management controls (edit %, forgive) on the orange piller table rows.

The CRUD layer already has `get_arrangement_by_merchant_wallet(wallet_id)` (returns single arrangement) and `update_arrangement(id, **kwargs)` (flexible field updates). Both are ready to use. The only gap is that `get_arrangement_by_merchant_wallet` uses `fetchone`, limiting a merchant to one arrangement — acceptable for MVP since S02's rerouting engine has the same assumption.

## Recommendation

**Single-page conditional rendering.** Both orange piller and merchant views live in the same `index.html` template. On page load, JS calls both `GET /api/v1/arrangements` (orange piller view) and `GET /api/v1/merchant/arrangements` (merchant view). Sections show/hide based on which returns data. This is simpler than a separate route/template and matches how the extension already works — one page, one wallet selector.

**PUT endpoint with two operations:**
- `reroute_percent` update: accepts new percent (1–100), only on active arrangements
- Forgiveness: sets `repaid_sats = total_debt_sats`, `status = "completed"` — effectively zeroes the debt

Both operations require `require_admin_key` and verify `key_info.wallet.id == arrangement.orange_piller_wallet` (only the orange piller who created the arrangement can modify it).

**Use a Pydantic request model** (`UpdateArrangement`) with optional fields: `reroute_percent: Optional[int]` and `forgive: Optional[bool]`. This is cleaner than separate endpoints and the `update_arrangement(**kwargs)` CRUD function already supports flexible field updates.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Flexible field update | `update_arrangement(id, **kwargs)` in crud.py | Already built in S01, handles any field combo |
| Merchant wallet lookup | `get_arrangement_by_merchant_wallet(wallet_id)` in crud.py | Built in S01 for S02's rerouting; reuse for merchant view |
| Wallet auth | `require_admin_key` decorator from lnbits.decorators | Standard LNbits pattern, returns `WalletTypeInfo` with `wallet.id` |
| Computed fields in JS | S03 pattern: `remaining_debt = a.total_debt_sats - a.repaid_sats` | Decision #6 mandates JS computation, S03 already has the mapping |
| Toast notifications | `LNbits.utils.notifyApiError(err)` and Quasar `$q.notify` | Already used in S03's `index.js` |

## Existing Code and Patterns

- `orangepiller/views_api.py` — PUT endpoint is a 501 stub at line ~80. Replace entirely. GET endpoint pattern to follow for the new merchant GET.
- `orangepiller/crud.py` — `update_arrangement(id, **kwargs)` accepts arbitrary fields; for forgiveness, call with `repaid_sats=arrangement.total_debt_sats, status="completed"`. `get_arrangement_by_merchant_wallet(wallet_id)` returns `Optional[Arrangement]`.
- `orangepiller/static/js/index.js` — S03 dashboard JS. Extend with: merchant arrangements data/methods, management dialog for edit/forgive. The `getArrangements()` method pattern is the template for `getMerchantArrangements()`.
- `orangepiller/templates/orangepiller/index.html` — S03 template with Quasar table. Add: merchant section (conditionally shown), action buttons column on orange piller table, edit dialog.
- `orangepiller/models.py` — Add `UpdateArrangement` request model here alongside `CreateArrangement`.
- `/tmp/splitpayments/views_api.py` — PUT pattern: `require_admin_key`, validate input, call CRUD. Simple and directly applicable.

## Constraints

- **Pydantic v1** — `Optional[int] = None` for optional fields, no `model_validator`. Use standard `__init__` or endpoint-level validation.
- **Decision #6** — Computed fields (`remaining_debt`, `progress_percent`) must be computed client-side in JS, not added to API responses. Both orange piller and merchant JS code must do this mapping.
- **Decision #2** — `update_arrangement` uses `**kwargs` for flexibility. Don't create separate update functions.
- **Single arrangement per merchant wallet** — `get_arrangement_by_merchant_wallet` uses `fetchone`. S02 rerouting depends on this assumption. Don't change to `fetchall` without also updating S02.
- **No new Python dependencies** — LNbits policy. Quasar components only for frontend.
- **`require_admin_key` for writes, `require_invoice_key` acceptable for reads** — Merchant view only needs read access. Could use `require_invoice_key` for the merchant GET endpoint (lower privilege), but `require_admin_key` is also fine and consistent.

## Common Pitfalls

- **Forgetting authorization on PUT** — The orange piller's wallet ID must match `arrangement.orange_piller_wallet`. Without this check, any authenticated user could modify any arrangement. Always fetch the arrangement first and compare wallet IDs.
- **Forgiveness on already-completed arrangement** — If the arrangement is already completed, forgiveness is a no-op but shouldn't error. Check `arrangement.status` and return the arrangement unchanged (or 400).
- **Editing reroute_percent on completed arrangement** — Should be rejected. Only active arrangements can have their percentage changed.
- **Race condition on forgiveness** — If a payment is being rerouted while the orange piller forgives, the reroute could complete after forgiveness. This is acceptable: the rerouting engine checks `WHERE status = 'active'` in its atomic UPDATE, so it will naturally skip if forgiveness set status to "completed" first. If the reroute's atomic UPDATE already ran, the forgiveness will see a slightly higher `repaid_sats` — harmless.
- **Merchant seeing stale data** — The merchant view should re-fetch on wallet change, same as the orange piller view. Use the same `watch: { selectedWallet }` pattern.

## Open Risks

- **Merchant with multiple orange pillers** — `get_arrangement_by_merchant_wallet` returns only one arrangement. If two orange pillers onboard the same merchant wallet, only one arrangement is returned to the merchant. Low risk for MVP (unlikely scenario), but worth a follow-up issue if needed.
- **No undo for forgiveness** — Once debt is forgiven (status set to "completed"), there's no reversal. The UI should have a confirmation dialog. This is a UX concern, not a technical risk.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| LNbits | — | No dedicated skill; extension patterns well-documented in codebase |
| Quasar/Vue.js | frontend-design | installed (available in `<available_skills>`) |
| FastAPI | — | Standard patterns; no skill needed |

No external skills needed — this is straightforward CRUD + UI work following established patterns.

## Sources

- `orangepiller/views_api.py` — Current PUT stub and GET pattern to follow
- `orangepiller/crud.py` — `update_arrangement` and `get_arrangement_by_merchant_wallet` already implemented
- `orangepiller/static/js/index.js` — S03 dashboard JS with computed field pattern
- `/tmp/splitpayments/views_api.py` — PUT endpoint pattern with admin key auth
- `lnbits/decorators.py` — `require_admin_key` returns `WalletTypeInfo` with `wallet.id`
- `lnbits/templates/base.html` — `window.g.user` provides user data including wallet IDs and admin keys to JS
- S01/S02 summaries — Forward intelligence on computed field serialization gap and CRUD contracts
