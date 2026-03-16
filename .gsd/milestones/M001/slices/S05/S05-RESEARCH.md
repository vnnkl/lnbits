# M001/S05 — Research

**Date:** 2026-03-16

## Summary

S05 covers three requirements: R008 (clean cutover), R009 (packaging), and R010 (completion signal). The surprising finding is that **R008 and R010 are already substantially implemented** by prior slices. S02's atomic SQL UPDATE in `crud.py` already transitions `status` to `"completed"` when `repaid_sats >= total_debt_sats`, and `on_invoice_paid` in `tasks.py` already skips completed arrangements. Both dashboards from S03/S04 already render green "Completed" chips and progress bars. The remaining S05 work is: (1) verify the cutover path works end-to-end, (2) optionally add a JS toast notification when completion is detected, and (3) complete the packaging gaps — config.json is missing `version`, `license`, `description_md`, `images`, and `terms_and_conditions_md`; the repo needs `README.md`, `LICENSE`, and `description.md` files.

LNbits has **no built-in notification system** that extensions can hook into. "Notification" for R010 means visual status change (already done) plus optionally a Quasar `$q.notify` toast triggered client-side when the dashboard detects a newly-completed arrangement. Push notifications or websocket alerts are out of scope.

## Recommendation

Treat S05 as primarily a **packaging and verification slice**, not a feature slice. The clean cutover logic is done. The work is:

1. **Packaging**: Add `version` field to `config.json`, create `README.md`, `LICENSE` (MIT), `description.md`, optionally `toc.md`. Ensure manifest.json matches the splitpayments pattern exactly.
2. **Completion notification**: Add a lightweight JS check — compare arrangement statuses before/after API refresh and show a Quasar toast for any arrangement that transitioned to "completed". This is cheap and satisfies R010's "notification if easy to implement".
3. **Tile image**: The config.json references `/orangepiller/static/bitcoin-extension.png` which doesn't exist. Create a simple placeholder or SVG.
4. **Verification**: Write a test that proves the cutover path — mock a payment that exactly completes the debt, assert status transitions to "completed", assert subsequent payments are skipped.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Extension packaging format | `/tmp/splitpayments/config.json` | Has all required fields; copy structure exactly |
| Notification toast | Quasar `$q.notify()` | Already used in index.js for edit/forgive confirmations |
| Completion detection in JS | Compare `status` before/after `getArrangements()` | Simple diff — no new dependencies |

## Existing Code and Patterns

- `orangepiller/crud.py` `update_arrangement_repaid()` — **Already handles cutover**: SQL CASE sets `status='completed'` when `repaid_sats + sats >= total_debt_sats`. No changes needed.
- `orangepiller/tasks.py` `on_invoice_paid()` — **Already skips completed arrangements**: checks `arrangement.status != "active"` before rerouting. No changes needed.
- `orangepiller/static/js/index.js` `_mapArrangement()` — Centralized computed field mapping. Add completion detection here or in `getArrangements()`.
- `orangepiller/templates/orangepiller/index.html` — Both piller and merchant tables already have status chip slots with green/orange coloring. No template changes needed for R008/R010 status display.
- `/tmp/splitpayments/config.json` — Reference for complete config.json with `version`, `description_md`, `images`, `license`, `terms_and_conditions_md` fields.
- `/tmp/splitpayments/README.md` — Reference for extension README format.
- `lnbits/core/models/extensions.py` `ExtensionConfig` — Parses `name`, `short_description`, `tile`, `warning`, `min_lnbits_version`, `max_lnbits_version` from config.json. The `version`, `images`, `license` etc. fields are used by the `ExplicitRelease` model for the extension manager.

## Constraints

- **No built-in notification system**: LNbits core has no extension-accessible notification API. Notifications are UI-only (Quasar toasts).
- **config.json must have `version` field**: The `ExplicitRelease` model requires it; `ExtensionConfig` doesn't but GitHub release fetching does.
- **Pydantic v1 `@property` not in `.dict()`**: Computed fields (`remaining_debt`, `progress_percent`, `is_completed`) stay in JS — confirmed by Decision #6.
- **No tile image exists**: `orangepiller/static/bitcoin-extension.png` referenced in config.json but `orangepiller/static/` only contains `js/`. Need to create or provide a placeholder.
- **pyproject.toml uses `[project]` format**: Splitpayments uses `[tool.poetry]`. Both work — LNbits doesn't parse pyproject.toml for extension loading; it only reads config.json.

## Common Pitfalls

- **Forgetting the tile image** — config.json references it; extension manager will show a broken image. Create a simple SVG or PNG placeholder.
- **manifest.json `id` must match directory name** — Currently `"id": "orangepiller"` which matches the directory. Don't change this.
- **config.json `min_lnbits_version` currently `"1.0.0"`** — Splitpayments uses `"1.3.0"`. Should check which LNbits version introduced the APIs we use (`create_user_account_no_ckeck`, `Database` class). Setting too low risks install failures.
- **Notification toast fires on every refresh, not just transitions** — Must track previous status and only notify when an arrangement *transitions* to completed, not when it's already completed.

## Open Risks

- **No integration test environment**: Proving the full cutover path (pay → reroute → debt zero → status change → skip subsequent) requires a running LNbits instance. Unit tests can prove the logic but not the integration.
- **Tile image format**: If LNbits extension manager expects PNG specifically (not SVG), a placeholder SVG won't work. Splitpayments uses PNG.

## Cutover Path Analysis (already implemented)

The complete cutover flow through existing code:

1. Payment arrives → `on_invoice_paid()` in tasks.py
2. Tag guard passes → arrangement looked up → status is "active" ✓
3. `reroute_sats = min(payment.sat * percent // 100, remaining_debt)` — caps at remaining
4. `update_arrangement_repaid(id, reroute_sats)` → SQL CASE: if `repaid_sats + sats >= total_debt_sats` → set `status = 'completed'`
5. Internal transfer executes (or rolls back on failure)
6. **Next payment**: `on_invoice_paid()` → arrangement looked up → `status != "active"` → **skipped** ✓
7. **Dashboard refresh**: API returns arrangement with `status: "completed"` → JS computes `progress_percent: "100.00"` → green chip shows "Completed" ✓

**No code changes needed for the cutover mechanic itself.**

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| LNbits | — | No skill found (niche project) |
| Quasar/Vue.js | — | Not needed (trivial toast addition) |

## Sources

- `orangepiller/crud.py` lines 56-80 — atomic update with CASE cap and status transition (local code inspection)
- `orangepiller/tasks.py` lines 29-37 — status check before rerouting (local code inspection)
- `lnbits/core/models/extensions.py` — ExtensionConfig and ExplicitRelease models (local code inspection)
- `/tmp/splitpayments/config.json` — reference packaging with all fields (local file)
- `/tmp/splitpayments/README.md` — reference README format (local file)
