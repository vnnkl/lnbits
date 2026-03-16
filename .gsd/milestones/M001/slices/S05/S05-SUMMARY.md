---
id: S05
parent: M001
milestone: M001
provides:
  - Clean cutover path: debt reaches zero → status "completed" → rerouting stops
  - Transition-aware toast notifications on both dashboards
  - Complete extension packaging for GitHub install (config.json, tile, README, LICENSE, description.md)
requires:
  - slice: S02
    provides: Atomic update_arrangement_repaid with status transition, on_invoice_paid skip logic
  - slice: S03
    provides: Dashboard template with status chips, getArrangements() JS function
  - slice: S04
    provides: Merchant view template with status display, getMerchantArrangements() JS function
affects: []
key_files:
  - orangepiller/config.json
  - orangepiller/static/image/orange-piller.png
  - orangepiller/README.md
  - orangepiller/LICENSE
  - orangepiller/description.md
  - orangepiller/static/js/index.js
  - tests/extensions/orangepiller/test_cutover.py
key_decisions:
  - Used empty images array in config.json — no screenshots yet, populate when UI is finalized
  - Generated solid-orange 256x256 PNG as tile placeholder — replace with branded artwork before public release
  - Extracted shared _detectCompletionTransitions() method for toast notifications, reused by both piller and merchant views
  - Status transition detection compares old vs new arrays by id — fires toast only on actual transition, not initial load
patterns_established:
  - Extension packaging follows splitpayments reference pattern (config.json fields, file layout)
  - Status transition detection pattern: snapshot old list, compare per-id after fetch, notify only on transition
observability_surfaces:
  - Client-side Quasar toast notification on arrangement completion transition
  - config.json parseable by LNbits ExtensionConfig model; missing fields cause install failure
  - test_cutover.py verifies server-side cutover path (run with pytest)
drill_down_paths:
  - .gsd/milestones/M001/slices/S05/tasks/T01-SUMMARY.md
  - .gsd/milestones/M001/slices/S05/tasks/T02-SUMMARY.md
duration: 16m
verification_result: passed
completed_at: 2026-03-16
---

# S05: Clean cutover, notifications & packaging

**Extension packaging complete with config.json/tile/README/LICENSE, completion toast notifications on both dashboards, and cutover path verified by 3 tests proving debt-zero → completed → skip**

## What Happened

**T01 (Packaging):** Added all required fields to `config.json` for the LNbits extension manager: version (0.1.0), license (MIT), description_md, images, terms_and_conditions_md, and set min_lnbits_version to 1.3.0. Generated a 256x256 solid-orange PNG tile image. Created README.md with install/usage documentation, MIT LICENSE file, and description.md for the extension manager gallery.

**T02 (Notifications & Cutover Tests):** Added `_detectCompletionTransitions(oldList, newList, labelFn)` to the Vue app — compares arrangement statuses before and after each API fetch, fires a Quasar positive toast when any arrangement transitions to "completed". Integrated into both `getArrangements()` (piller view) and `getMerchantArrangements()` (merchant view). Created `test_cutover.py` with 3 tests proving: (1) payment triggers atomic update and status becomes "completed" when repaid >= total, (2) completed arrangements are skipped with no update or transfer, (3) exact payoff caps at remaining debt and completes.

## Verification

- `python -m pytest tests/extensions/orangepiller/test_cutover.py -v` — **3/3 passed** (0.56s)
- `config.json` validation (version, license, description_md fields present) — **PASS**
- `orangepiller/static/image/orange-piller.png` exists (852 bytes) — **PASS**
- `orangepiller/README.md`, `LICENSE`, `description.md` all exist — **PASS**
- `grep -q 'notify' orangepiller/static/js/index.js` — **PASS** (7 occurrences)
- Extension config import — deferred to UAT (requires full LNbits runtime)

## Requirements Advanced

- R008 (Clean cutover) — Proven by test suite: debt reaches zero → status "completed" → subsequent payments skipped. Rerouting stops automatically.
- R009 (Standalone extension packaging) — config.json, tile image, README, LICENSE, description.md all present following splitpayments pattern. min_lnbits_version set to 1.3.0.
- R010 (Repayment completion signal) — Toast notifications fire on both dashboards when arrangement transitions to "completed". Status chips already show completion state (from S03/S04).

## Requirements Validated

- R008 — 3 cutover tests prove debt-zero → completed → skip path; contract-level verification complete
- R009 — All packaging artifacts present and config.json validates; install test deferred to UAT
- R010 — Toast notification code present and transition-aware; visual verification deferred to UAT

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

- T02 toast message uses `merchant_wallet` / `orange_piller_wallet` identifiers instead of arrangement `id` as originally planned — more meaningful to users
- Tests exercise cutover through `on_invoice_paid` (integration-level mocks) rather than calling `update_arrangement_repaid` directly, since the CRUD function requires a real DB connection

## Known Limitations

- `images` array in config.json is empty — no UI screenshots available yet
- Tile image is a solid orange placeholder — needs proper branded artwork before public release
- Extension config import test requires full LNbits runtime — deferred to milestone-level UAT

## Follow-ups

- Replace placeholder tile image with branded artwork
- Populate config.json `images` array with UI screenshots
- Milestone-level UAT: install extension from GitHub on clean LNbits instance, run full end-to-end flow

## Files Created/Modified

- `orangepiller/config.json` — added version, license, description_md, images, terms_and_conditions_md, updated min_lnbits_version and tile path
- `orangepiller/static/image/orange-piller.png` — 256x256 solid-orange PNG tile image (generated)
- `orangepiller/README.md` — extension documentation with features, install, and usage sections
- `orangepiller/LICENSE` — MIT license
- `orangepiller/description.md` — short description for extension manager gallery
- `orangepiller/static/js/index.js` — added `_detectCompletionTransitions()` method, integrated into both dashboard fetch functions
- `tests/extensions/orangepiller/test_cutover.py` — 3 cutover-path tests

## Forward Intelligence

### What the next slice should know
- All 5 slices are complete. The next step is milestone-level UAT on a running LNbits instance.
- The extension is structurally complete but has not been tested as an installed GitHub extension yet.

### What's fragile
- Toast notification relies on comparing array snapshots by `id` field — if the API response shape changes (e.g., `id` renamed), transitions won't detect properly.
- Placeholder tile image will show as a solid orange square in the extension manager — functional but visually poor.

### Authoritative diagnostics
- `python -m pytest tests/extensions/orangepiller/ -v` — runs all extension tests (onboarding, rerouting, cutover)
- `orangepiller/config.json` — single source of truth for extension manager metadata
- Server logs with `orangepiller:` prefix — shows rerouting decisions and completion transitions

### What assumptions changed
- min_lnbits_version set to 1.3.0 (matches splitpayments) rather than 1.5.x — broader compatibility
