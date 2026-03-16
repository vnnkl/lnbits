# S02 — Research: Dashboards, QR codes & printable poster

**Date:** 2026-03-16

## Target Requirements

- **R104** — TPoS link and QR on dashboards (primary owner)
- **R105** — Printable merchant poster with QR code (primary owner)
- **R106** — Merchant login credentials surfaced to orange piller (supporting — credentials already stored by S01, S02 surfaces them in the UI)

## Summary

This slice adds three things: (1) TPoS link + QR code columns to both dashboards, (2) a "Print poster" button on the orange piller dashboard, and (3) a standalone poster page at `/orangepiller/poster/{arrangement_id}`. The codebase is well-prepared — S01 already populates `tpos_url`, `merchant_name`, and `merchant_credentials` on the Arrangement model and stores them in the DB. The GET endpoints return these fields via `SELECT *`. The work is purely frontend template + JS changes, plus one new view route for the poster.

LNbits provides everything needed: a global `<lnbits-qrcode>` Vue component (wrapping `qrcode-vue` v3.6.0), a `print.html` base template stripped of LNbits chrome but with Quasar/Vue/QR components available, and Quasar's full component library for dialogs and layout. No new Python dependencies, no new migrations, no new API endpoints needed — just a new HTML view route and template/JS changes.

The lowest-risk approach is: (1) add columns to existing table definitions in `index.js`, (2) add QR-dialog and poster-link affordances to the template, (3) create a new `/poster/{arrangement_id}` view route that fetches the arrangement and renders `poster.html`, (4) create the poster template extending `print.html`. All QR rendering happens client-side via the existing `<lnbits-qrcode>` component.

## Recommendation

**Use existing LNbits patterns everywhere — no custom QR rendering, no new dependencies.**

- Dashboard QR: Show `tpos_url` as a clickable link in the table. Add a QR icon button that opens a Quasar `<q-dialog>` containing `<lnbits-qrcode :value="row.tpos_url">`. This reuses the exact same component LNbits core uses for wallet QR codes (includes copy, download SVG, and print buttons for free).
- Poster: New view route `/orangepiller/poster/{arrangement_id}` — unauthenticated (arrangement IDs are 22-char base57 shortuuids, unguessable). Template extends `print.html` which gives us Quasar/Vue and `<lnbits-qrcode>` without LNbits header/drawer/footer. Arrangement data passed as template context; Vue reads it from a `<script>` block. Print-optimized CSS via `@page` and `@media print` rules.
- Merchant credentials: Show `merchant_credentials` (the login URL) as a copyable chip/link on the orange piller dashboard.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| QR code rendering | `<lnbits-qrcode :value="url">` component (wraps `qrcode-vue` v3.6.0) | Already bundled in LNbits vendor JS; includes copy, download SVG, print, NFC buttons. Available on all pages that load `components.vue` (both `base.html` and `print.html`). |
| Print-optimized page layout | `lnbits/templates/print.html` base template | Strips all LNbits chrome (no header, drawer, footer) while keeping Quasar, Vue, and all component JS available. Already has `@page { size: A4 portrait }` CSS. |
| Dialog for QR display | Quasar `<q-dialog>` | Already available via Quasar UMD; well-supported pattern in the extension's existing edit/forgive dialogs. |
| Copy to clipboard | `this.utils.copyText(value)` from `windowMixin` | Standard LNbits pattern available via the mixin; no external clipboard library needed. |
| Template rendering | `template_renderer(["orangepiller/templates"])` | Existing pattern in `views.py`; adds extension template directory to Jinja2 search path so `print.html` resolves from core templates while `orangepiller/poster.html` resolves from extension templates. |

## Existing Code and Patterns

- `orangepiller/templates/orangepiller/index.html` — Dashboard template with two `q-table` sections (orange piller + merchant). Pattern: body-cell slots for custom rendering (progress bars, status chips, action buttons). Add new columns for TPoS/QR/poster here.
- `orangepiller/static/js/index.js` — Vue app with `columns` and `merchantColumns` array definitions. Pattern: columns defined in `data()`, computed fields added in `_mapArrangement()`. Add new column definitions here.
- `orangepiller/views.py` — Single view route (`/` → `index.html`). Pattern: `APIRouter` + `template_renderer`. Add new poster route here.
- `orangepiller/crud.py` — `get_arrangement(id)` already exists for fetching by arrangement ID. Poster view can reuse this directly.
- `lnbits/templates/print.html` — Standalone print template. Pattern: extends nothing, includes `components.vue` and all vendor JS. Poster template should extend this.
- `lnbits/templates/components/lnbits-qrcode.vue` — QR component template. Props: `value` (required), `showButtons` (default true), `maxWidth` (default 450), `print`, `nfc`. For poster, use `maxWidth=600` and `showButtons=false` (poster is the print artifact itself).
- `lnbits/static/js/components/lnbits-qrcode.js` — QR component JS. Key: `QrcodeVue` is registered globally from `qrcode.vue.browser.js` vendor bundle. No import needed.
- `lnbits/templates/macros.jinja` — `window_vars(user)` macro creates the Vue app. Poster page needs its own `Vue.createApp()` since there's no user context.

## Constraints

- **No new Python dependencies** — QR generation must be client-side via existing `qrcode-vue` v3.6.0
- **Pydantic v1 (1.10.x)** — Arrangement model uses `.dict()` for serialization; `@property` fields (`remaining_debt`, `progress_percent`) are NOT included in dict output (Decision #6)
- **`tpos_url` can be null** — Template must handle arrangements where TPoS was not provisioned (show informative message instead of broken QR; check `tpos_url` presence, not `warning` field which is response-only and not persisted per S01 Forward Intelligence)
- **`merchant_credentials` is always populated** — Safe to always render (per S01 Forward Intelligence)
- **`warning` field is NOT available on GET responses** — It's `no_database=True`, set only on POST response. Dashboard must check `tpos_id === null` to detect missing TPoS.
- **Extension template resolution** — `template_renderer(["orangepiller/templates"])` adds extension templates to Jinja2 search, but core templates (`print.html`) are always in the base search path
- **Poster is unauthenticated** — Arrangement IDs are 22-char base57 shortuuids (~128 bits entropy); unguessable. Poster route does NOT use `check_user_exists`.
- **SQLite + PostgreSQL** — No new DB changes needed (S01 migration covers all fields), but query patterns must remain compatible

## Common Pitfalls

- **Rendering QR for null tpos_url** — The `<lnbits-qrcode>` component requires a non-empty `value` prop. Passing null/empty will break rendering. Always guard with `v-if="row.tpos_url"` and show a "No TPoS" message otherwise.
- **Poster Vue app initialization** — The poster page extends `print.html`, not `base.html`. The `window_vars(user)` macro from `base.html` won't be called. The poster JS must create its own Vue app: `window.app = Vue.createApp({...})` then wait for component registration via `INCLUDED_COMPONENTS` scripts. The pattern is: `window.app` must exist before component scripts run. The poster `<script>` block should create the app first (like the macro does), then the extension script mounts it.
- **Dialog QR vs inline QR** — Inline QR codes in table cells make the table unreadable. Use a dialog triggered by an icon button. The dialog pattern already exists (edit/forgive dialogs).
- **Print CSS for poster** — `print.html` sets `@page { size: A4 portrait }` but the poster needs additional `@media print` rules to hide any non-essential elements and ensure the QR is large and centered.
- **Poster arrangement not found** — If the arrangement ID doesn't exist, the poster view should return 404. Use `get_arrangement()` and check for `None`.
- **Poster with no TPoS URL** — If the arrangement has no `tpos_url`, the poster can't show a QR. The poster view should either return 404 or show a "No payment terminal" message.

## Open Risks

- **Poster security** — The poster URL leaks the arrangement ID, which could theoretically be used to look up arrangement details if other endpoints don't properly auth-gate. Current API endpoints all require admin key, so the risk is minimal. But the poster itself reveals merchant_name and tpos_url — these are intended to be public (they go on a physical poster at the merchant's counter).
- **QR code scannability at print resolution** — `qrcode-vue` renders SVG, which scales perfectly for print. But the `<lnbits-qrcode>` component logo overlay might reduce QR readability at smaller sizes. For the poster, consider `showButtons=false` and potentially no logo overlay. Error correction level "Q" (25%) is already set in the component template, which allows for logo overlay.
- **Component loading order** — The poster page relies on `qrcode.vue.browser.js` being loaded before `lnbits-qrcode.js`. Both come via `INCLUDED_JS` and `INCLUDED_COMPONENTS` respectively, and the template loads them in that order (`INCLUDED_JS` first, then `INCLUDED_COMPONENTS`). This matches `print.html`'s script loading order.

## Architecture Sketch

### Dashboard Changes (index.html + index.js)

**Orange piller table — new columns:**
1. `merchant_name` — text column (simple field display)
2. `tpos` — custom body-cell slot: clickable link icon + QR icon button (opens dialog) + poster link icon. Show "No TPoS" chip when `tpos_url` is null.
3. `merchant_credentials` — copy button with the login URL

**Merchant table — new column:**
1. `tpos` — clickable TPoS link + QR icon button. Simpler than orange piller view (no poster, no credentials).

**New dialog:**
- `showQrDialog` + `qrDialogUrl` data fields
- `<q-dialog>` containing `<lnbits-qrcode :value="qrDialogUrl" :show-buttons="true">`

### Poster Route (views.py)

```
GET /orangepiller/poster/{arrangement_id} → poster.html
```
- No auth (public page)
- Fetches arrangement via `get_arrangement()`
- 404 if arrangement not found or `tpos_url` is null
- Passes `arrangement` data as template context

### Poster Template (poster.html)

```
{% extends "print.html" %}
```
- Clean page: merchant name (large heading), "Pay with Bitcoin" subtitle, large QR code via `<lnbits-qrcode>`, LNbits branding footer
- `@media print` CSS to remove margins, maximize QR size
- Vue app reads arrangement data from server-injected `<script>` context

### File Changes Summary

| File | Change |
|------|--------|
| `orangepiller/static/js/index.js` | Add columns, QR dialog data/methods, poster link helper |
| `orangepiller/templates/orangepiller/index.html` | Add QR dialog, new table column slots, merchant_credentials display |
| `orangepiller/templates/orangepiller/poster.html` | **New file** — poster template extending print.html |
| `orangepiller/views.py` | Add poster route `GET /poster/{arrangement_id}` |

No changes to: `models.py`, `crud.py`, `views_api.py`, `migrations.py`, `__init__.py`, `tasks.py`

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| LNbits | none | no skills found |
| Quasar/Vue | `harlan-zw/vue-ecosystem-skills@quasar-skilld` | available (72 installs) |
| Vue | `jeffallan/claude-skills@vue-expert` | available (756 installs) |

## Sources

- `lnbits-qrcode` component: `lnbits/static/js/components/lnbits-qrcode.js` + `lnbits/templates/components/lnbits-qrcode.vue` — props: value, showButtons, maxWidth, print, nfc, logo, margin
- `print.html` base template: `lnbits/templates/print.html` — standalone print page with Quasar/Vue/components, no LNbits chrome
- `qrcode-vue` v3.6.0: `lnbits/static/vendor/qrcode.vue.browser.js` — globally available as `QrcodeVue`
- Arrangement model fields (S01): `tpos_url`, `merchant_name`, `merchant_credentials`, `tpos_id` — all nullable, all returned by GET endpoints via `SELECT *`
- S01 Forward Intelligence: `tpos_url` null when TPoS absent; `merchant_credentials` always populated; `warning` field not on GET responses — check `tpos_id === null` for missing TPoS detection
