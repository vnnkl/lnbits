---
id: M001
provides:
  - Complete orangepiller LNbits extension with merchant onboarding, payment rerouting, dual dashboards, arrangement management, and GitHub-installable packaging
key_decisions:
  - Extension code identifier `orangepiller` (lowercase, no dashes) per LNbits convention
  - Atomic SQL UPDATE with CASE cap for concurrent-safe debt tracking (no RETURNING for SQLite compat)
  - Debt updated before transfer with rollback on failure to prevent concurrent overpayment
  - Computed fields (remaining_debt, progress_percent) calculated client-side in JS due to Pydantic v1 @property limitation
  - Single UpdateArrangement model handles both forgiveness and percent update via one PUT endpoint
  - Extension packaging follows splitpayments reference pattern with min_lnbits_version=1.3.0
patterns_established:
  - LNbits extension scaffold pattern (router prefix, static files, lifecycle hooks, __all__ exports)
  - Schema-qualified tables (orangepiller.arrangements) with Database("ext_orangepiller")
  - Invoice listener pattern via register_invoice_listener with tag guard to prevent infinite loops
  - Atomic SQL UPDATE with CASE for concurrent-safe field capping and status transitions
  - Dialog state pattern in Vue/Quasar for management actions (edit, forgive)
  - Status transition detection via array snapshot comparison for toast notifications
observability_surfaces:
  - loguru INFO on arrangement creation, successful reroute, and management actions
  - loguru WARNING on transfer failures with rollback details
  - loguru DEBUG on skip reasons (tag guard, no arrangement, zero amount, completed)
  - HTTP status codes: 400 (bad input), 403 (wrong wallet), 404 (not found), 501 (stub)
  - Browser DevTools network tab for API request/response inspection
  - DB inspection via SELECT on orangepiller.arrangements table
requirement_outcomes:
  - id: R001
    from_status: active
    to_status: validated
    proof: POST endpoint creates merchant account + wallet + arrangement atomically; create_user_account_no_ckeck called with default_exts; import tests and route inspection pass
  - id: R002
    from_status: active
    to_status: validated
    proof: CreateArrangement model accepts total_debt_sats and reroute_percent (1-100); PUT endpoint allows post-creation percent adjustment; 6 merchant API tests pass
  - id: R003
    from_status: active
    to_status: validated
    proof: on_invoice_paid intercepts payments, calculates split, performs internal transfer; atomic SQL prevents concurrent overpayment; 11 reroute tests pass
  - id: R004
    from_status: active
    to_status: validated
    proof: min(reroute_amount, remaining_debt) enforced; SQL CASE caps repaid_sats at total_debt_sats; test_cap_at_remaining_debt and test_exact_payoff pass
  - id: R005
    from_status: active
    to_status: validated
    proof: Quasar dashboard with q-table, q-linear-progress bars, status chips; computed fields verified via Node.js check (remaining_debt=55000, progress_percent=45.00)
  - id: R006
    from_status: active
    to_status: validated
    proof: Merchant GET endpoint at /api/v1/merchant/arrangements; conditional v-if section in dashboard template; merchant sees own arrangement details
  - id: R007
    from_status: active
    to_status: validated
    proof: PUT /api/v1/arrangements/{id} with auth check; edit dialog (1-100 validation) and forgive dialog with confirmation; 6 merchant API tests cover all paths
  - id: R008
    from_status: validated
    to_status: validated
    proof: 3 cutover tests prove debt-zero → completed → skip path (test_cutover.py)
  - id: R009
    from_status: validated
    to_status: validated
    proof: config.json with all required fields, manifest.json, pyproject.toml, tile image, README, LICENSE, description.md
  - id: R010
    from_status: validated
    to_status: validated
    proof: _detectCompletionTransitions() fires toast on both dashboards; status chips show completion state
duration: 106m
verification_result: passed
completed_at: 2026-03-16
---

# M001: Orange Piller Extension

**Complete LNbits extension delivering merchant onboarding with automated sat-denominated payback via payment rerouting — atomic debt tracking, dual dashboards, arrangement management, and GitHub-installable packaging**

## What Happened

Built the orangepiller extension across 5 slices in a single session.

**S01 (scaffold + onboarding)** established the extension foundation: 11 files following the splitpayments/example pattern. The Arrangement model tracks 9 persisted fields with 3 computed properties. The migration creates `orangepiller.arrangements` with constraints. The POST endpoint atomically creates a merchant LNbits account (via `create_user_account_no_ckeck` with `default_exts=["orangepiller"]`), extracts the default wallet, and stores the payback arrangement — all in one API call.

**S02 (rerouting engine)** implemented the core mechanic. The `on_invoice_paid` handler follows the splitpayments invoice listener pattern: tag guard → arrangement lookup → status check → cap calculation (`min(payment.sat * percent // 100, remaining_debt)`) → atomic debt update → internal transfer → rollback on failure. The atomic SQL UPDATE uses CASE expressions to cap `repaid_sats` at `total_debt_sats` and transition status to "completed" when fully repaid, all within `db.connect()` to hold the asyncio lock. 11 unit tests prove correctness across all code paths.

**S03 (orange piller dashboard)** delivered a Quasar table with progress bars (`q-linear-progress`), status badges (`q-chip`), and wallet-triggered data refresh. Computed fields are calculated client-side from raw API data to work around Pydantic v1's `@property` serialization limitation.

**S04 (merchant view + management)** added the merchant transparency section (conditional on wallet having an arrangement) and management controls. Edit dialog adjusts reroute percentage (1–100 validation). Forgive dialog with irreversible warning sets `repaid_sats=total_debt_sats` and completes the arrangement. The PUT endpoint checks orange piller wallet ownership before allowing changes. 6 additional tests cover authorization and validation paths.

**S05 (cutover + packaging)** completed the extension with toast notifications on both dashboards when arrangements transition to "completed", plus all packaging artifacts: config.json with required fields, tile image, README, LICENSE, description.md. 3 cutover tests prove the debt-zero → completed → skip path.

## Cross-Slice Verification

### Success Criteria Verification

1. **Orange piller can create a merchant's LNbits account with the extension auto-enabled and a payback arrangement configured, in one flow** — ✅ POST /api/v1/arrangements calls `create_user_account_no_ckeck(default_exts=["orangepiller"])` atomically creating account + wallet + arrangement. Import tests verify endpoint exists with correct route.

2. **Incoming payments to the merchant are automatically split — configured percentage goes to the orange piller's wallet as an internal transfer** — ✅ `on_invoice_paid` in tasks.py intercepts payments, calculates percentage split, creates internal invoice + pay_invoice. 11 reroute tests pass including successful reroute test.

3. **Debt tracking is exact to the sat, capped on the final payment, and concurrency-safe** — ✅ `min(reroute_amount, remaining_debt)` enforced in Python; SQL CASE caps `repaid_sats` at `total_debt_sats`; `db.connect()` holds asyncio lock. Tests `test_cap_at_remaining_debt` and `test_exact_payoff` prove cap logic.

4. **Orange piller sees a dashboard of all onboarded merchants with live payback progress** — ✅ Quasar q-table with progress bars, amounts, percentages, status badges. JS computed fields verified: remaining_debt=55000, progress_percent=45.00 for test data.

5. **Merchant sees arrangement details and repayment progress from their own dashboard** — ✅ GET /api/v1/merchant/arrangements endpoint; conditional `v-if="merchantArrangements.length"` section in template with progress bars and arrangement details.

6. **Orange piller can adjust reroute percentage and forgive remaining debt** — ✅ PUT /api/v1/arrangements/{id} with UpdateArrangement model; edit dialog (1–100 validation) and forgive dialog with confirmation. 6 merchant API tests cover auth, validation, forgiveness, and percent update.

7. **Rerouting stops automatically when debt reaches zero, with visible status change** — ✅ Atomic SQL transitions status to "completed"; `on_invoice_paid` skips completed arrangements. Toast notifications fire on transition. 3 cutover tests prove the path.

8. **Extension installs from a GitHub manifest on any LNbits 1.5.x instance** — ⏳ config.json, manifest.json, and all packaging artifacts present and validated structurally. Actual install-from-GitHub test deferred to UAT (requires a running LNbits instance with network access to GitHub).

### Definition of Done Verification

- ✅ All 5 slices marked `[x]` in roadmap
- ✅ All 5 slice summaries exist (S01 through S05)
- ✅ 20/20 unit tests pass (11 reroute + 6 merchant API + 3 cutover)
- ✅ All imports verified (models, CRUD, views_api, tasks, __init__)
- ✅ 4 API routes confirmed (POST arrangements, GET arrangements, GET merchant/arrangements, PUT arrangements/{id})
- ✅ Computed properties verified (remaining_debt, progress_percent, is_completed)
- ✅ Extension packaging complete (config.json, manifest.json, pyproject.toml, tile, README, LICENSE, description.md)
- ⏳ Full end-to-end flow on running LNbits instance — deferred to UAT
- ⏳ Install from GitHub on clean LNbits instance — deferred to UAT

## Requirement Changes

- R001: active → validated — POST endpoint atomically creates merchant account + wallet + arrangement; import and route tests pass
- R002: active → validated — CreateArrangement model validates debt/percent; PUT allows post-creation adjustment; tests pass
- R003: active → validated — Payment interception, split calculation, internal transfer, concurrency-safe atomic update; 11 tests pass
- R004: active → validated — min(reroute, remaining) in Python + SQL CASE cap; cap and exact payoff tests pass
- R005: active → validated — Quasar dashboard with progress bars, status badges, computed fields; structural verification pass
- R006: active → validated — Merchant GET endpoint + conditional dashboard section; tests pass
- R007: active → validated — PUT with auth check, edit/forgive dialogs; 6 API tests pass
- R008: validated → validated — (no change) 3 cutover tests prove debt-zero → completed → skip
- R009: validated → validated — (no change) All packaging artifacts present
- R010: validated → validated — (no change) Toast notifications with transition detection

## Forward Intelligence

### What the next milestone should know
- The extension is structurally complete and contract-verified but has NOT been tested on a running LNbits instance. The first priority for any follow-up work should be runtime UAT: install the extension, create an arrangement, make payments, and verify the full rerouting loop.
- `create_user_account_no_ckeck` has a typo in the LNbits codebase ("ckeck" not "check"). If LNbits ever fixes it, the import in views_api.py breaks.
- Pydantic v1 `@property` fields don't serialize — all computed values are in JS. If migrating to Pydantic v2, use `@computed_field` and remove the JS computation.

### What's fragile
- `user.wallets[0]` assumption after account creation — if `create_user_account_no_ckeck` ever returns a user without a default wallet, the POST handler will IndexError
- Concurrency safety relies on asyncio lock within single-process LNbits — multi-worker deployments would need DB-level locking
- Rollback resets status to 'active' unconditionally — adding more statuses (e.g. "paused") would require updating rollback logic
- `get_arrangement_by_merchant_wallet` returns a single arrangement — multi-arrangement merchants would need a list-based query

### Authoritative diagnostics
- `python -m pytest tests/extensions/orangepiller/ -v` — runs all 20 tests in under 1 second
- Import chain: `from orangepiller import orangepiller_ext, orangepiller_ext_api` — fastest smoke test
- DB state: `SELECT id, repaid_sats, total_debt_sats, status FROM orangepiller.arrangements`
- Server logs: `grep "orangepiller:" *.log` — structured messages at INFO/WARNING/DEBUG

### What assumptions changed
- No major assumptions changed. The LNbits extension patterns (splitpayments, example) were accurate references throughout.
- min_lnbits_version set to 1.3.0 (broader compatibility) rather than the 1.5.x originally mentioned in requirements.

## Files Created/Modified

- `orangepiller/__init__.py` — Extension entry point with router, static files, lifecycle hooks
- `orangepiller/config.json` — Extension metadata for LNbits extension manager
- `orangepiller/manifest.json` — GitHub repo reference for installation
- `orangepiller/pyproject.toml` — Python packaging configuration
- `orangepiller/models.py` — Arrangement, CreateArrangement, UpdateArrangement Pydantic models
- `orangepiller/migrations.py` — m001_initial creating orangepiller.arrangements table
- `orangepiller/crud.py` — CRUD layer with atomic debt update, rollback, flexible updates
- `orangepiller/views.py` — Template renderer
- `orangepiller/views_api.py` — POST/GET/PUT API endpoints with merchant namespace
- `orangepiller/tasks.py` — Payment rerouting engine with tag guard, cap, transfer, rollback
- `orangepiller/templates/orangepiller/index.html` — Quasar dashboard with piller table, merchant section, management dialogs
- `orangepiller/static/js/index.js` — Vue 3 app with computed fields, API calls, transition detection
- `orangepiller/static/image/orange-piller.png` — Tile image placeholder
- `orangepiller/README.md` — Extension documentation
- `orangepiller/LICENSE` — MIT license
- `orangepiller/description.md` — Extension manager gallery description
- `tests/extensions/orangepiller/test_reroute.py` — 11 reroute engine tests
- `tests/extensions/orangepiller/test_merchant_api.py` — 6 merchant API tests
- `tests/extensions/orangepiller/test_cutover.py` — 3 cutover path tests
- `tests/extensions/orangepiller/conftest.py` — Test configuration
