# M001/S03 — Research

**Date:** 2026-03-16

## Summary

S03 delivers the orange piller dashboard (R005). The scope is narrow: a Quasar/Vue.js frontend that lists all arrangements for the authenticated wallet with progress bars, amounts, percentages, and status indicators. The API endpoint (`GET /api/v1/arrangements`) already exists from S01, and the template/static file infrastructure is wired in `__init__.py`. The main work is: (1) fix the serialization gap where `@property` computed fields (`remaining_debt`, `progress_percent`, `is_completed`) don't appear in Pydantic v1 `.dict()` output, so the API must return them explicitly; (2) build the Quasar template with arrangement cards/table; (3) write the Vue.js `index.js` to fetch and display data.

The splitpayments extension provides the exact pattern to follow: `index.html` extends `base.html`, uses `window_vars(user)`, loads a separate `static/js/index.js`, and uses `LNbits.api.request()` with wallet admin keys for API calls. The `g.user.wallets` array is available in the Vue app via the `windowMixin`. No new dependencies or complex patterns are needed — this is pure frontend work on existing infrastructure.

## Recommendation

1. **Fix the serialization gap first.** Create an `ArrangementResponse` model (or override the GET endpoint to manually add computed fields to each arrangement dict). The cleanest approach: add a `.to_response_dict()` method on `Arrangement` that calls `.dict()` and adds the three computed properties, then use that in the GET endpoint. This keeps the model changes minimal and doesn't break S02's usage.

2. **Use a q-table for the arrangement list** rather than individual cards. Tables are the standard LNbits pattern for listing entities, they handle empty states and sorting, and they compress more information into less space. Add a `q-linear-progress` bar in a custom column slot for visual payback progress.

3. **Follow splitpayments pattern exactly**: `index.html` with `window_vars(user)` in `{% block scripts %}`, separate `static/js/index.js` loaded via `<script>` tag, `Vue.createApp` with `windowMixin`, wallet selection via `g.user.wallets`, API calls via `LNbits.api.request('GET', '/orangepiller/api/v1/arrangements', wallet.adminkey)`.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| API HTTP calls | `LNbits.api.request(method, url, apiKey)` | Handles auth headers, axios wrapping — used by every extension |
| User/wallet context | `windowMixin` + `g.user.wallets` | Global mixin injected by base.html, provides wallet list and selection |
| Table rendering | `q-table` Quasar component | Built-in sorting, pagination, empty state, custom column slots |
| Progress visualization | `q-linear-progress` Quasar component | Native Quasar, supports color, label, animation |
| Status badges | `q-badge` or `q-chip` Quasar component | Standard way to show active/completed status |
| Notifications | `Quasar.Notify.create()` | Used by splitpayments for user feedback |

## Existing Code and Patterns

- `orangepiller/views_api.py` — GET `/api/v1/arrangements` already returns arrangements filtered by authenticated wallet. Needs serialization fix for computed properties.
- `orangepiller/views.py` — Stub template renderer with `check_user_exists` dependency and `template_renderer(["orangepiller/templates"])`. Ready to use.
- `orangepiller/__init__.py` — Static files already mounted at `/orangepiller/static` via `orangepiller_static_files`. Just need to create `orangepiller/static/js/index.js`.
- `orangepiller/templates/orangepiller/index.html` — Placeholder template. Must be replaced with full Quasar dashboard.
- `/tmp/splitpayments/templates/splitpayments/index.html` — Reference for template structure: extends base.html, window_vars in scripts block, loads JS from static path.
- `/tmp/splitpayments/static/js/index.js` — Reference for Vue app pattern: `Vue.createApp`, `windowMixin`, `selectedWallet`, `LNbits.api.request`.
- `/tmp/example/templates/example/index.html` — Uses `static_url_for('example/static', path='js/index.js')` for JS path. Splitpayments uses direct path `/splitpayments/static/js/index.js` — either works.
- `lnbits/static/js/api.js` — Defines `LNbits.api.request(method, url, apiKey, data)` using axios.
- `lnbits/templates/macros.jinja` — `window_vars(user)` macro creates a default Vue app. Extensions override this by defining their own `window.app = Vue.createApp(...)` after the macro call.

## Constraints

- **Pydantic v1 serialization**: `@property` fields (`remaining_debt`, `progress_percent`, `is_completed`) are NOT included in `.dict()` or JSON serialization. The API response currently omits these. Must fix before frontend can use them.
- **No npm/build step**: All frontend code must be vanilla JS loaded via `<script>` tags. Vue 3 and Quasar are available globally from LNbits base template.
- **Admin key required**: `GET /api/v1/arrangements` uses `require_admin_key` — the frontend must send the wallet's `adminkey`, not `inkey`.
- **Vue 3 Composition API available but not required**: LNbits extensions use Options API (`data()`, `methods`, `created`). Follow this pattern for consistency.
- **Template rendering**: Must use Jinja2 `{% extends "base.html" %}` with `{% block page %}` and `{% block scripts %}`. The `window_vars(user)` macro must be called in scripts block.

## Common Pitfalls

- **Missing computed fields in API response** — The `response_model=list[Arrangement]` on the GET endpoint will serialize via `.dict()` which excludes `@property` fields. Either add a response dict helper or compute them in JS. Computing in JS is simpler and avoids touching the model/API contract that S02 depends on.
- **Wrong API path prefix** — The API router has `prefix="/api/v1"` but it's mounted under the extension router at `/orangepiller`. So the full path is `/orangepiller/api/v1/arrangements`. Must use this in JS fetch calls.
- **Wallet selection mismatch** — The orange piller may have multiple wallets. Only one will have arrangements. The dashboard should either auto-select the right wallet or show arrangements across all wallets. Current API filters by single wallet — need wallet selector like splitpayments.
- **Static directory missing** — `orangepiller/static/` exists as a directory but has no files yet. Must create `orangepiller/static/js/index.js`.

## Open Risks

- **Computed fields strategy**: Two options — (A) fix API to include computed fields, or (B) compute `remaining_debt` and `progress_percent` in JavaScript from `total_debt_sats` and `repaid_sats`. Option B is zero-risk (no backend changes) and the formulas are trivial. Recommend option B to avoid touching any code S02 depends on.
- **Wallet-scoped view**: If the orange piller used different wallets for different arrangements, they'd need to switch wallets to see all. This is the same UX pattern as splitpayments — acceptable for now.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Quasar/Vue.js | n/a | Built into LNbits — no external skill needed |
| LNbits extensions | n/a | Patterns fully documented in splitpayments + example |
| Jinja2 templates | n/a | Standard Python templating — no skill needed |

No skill discovery search needed — this slice is pure LNbits-internal frontend work using patterns already present in reference extensions.

## Sources

- Splitpayments extension template and JS (source: `/tmp/splitpayments/`)
- Example extension scaffold (source: `/tmp/example/`)
- LNbits API client (source: `lnbits/static/js/api.js`)
- LNbits template macros (source: `lnbits/templates/macros.jinja`)
- Pydantic v1 serialization behavior confirmed via local test — `.dict()` excludes `@property` fields
