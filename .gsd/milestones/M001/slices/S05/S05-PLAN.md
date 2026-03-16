# S05: Clean cutover, notifications & packaging

**Goal:** Debt reaches zero → rerouting stops automatically, status changes to "completed" on both dashboards with a toast notification. Extension repo has complete config.json, manifest.json, README, LICENSE, and is installable from GitHub.

**Demo:** Run the cutover verification test proving: payment completes debt → status transitions to "completed" → subsequent payments are skipped. Open extension page → both dashboards show green "Completed" chips. config.json has all required fields, tile image exists, README and LICENSE present.

## Must-Haves

- config.json has `version`, `license`, `description_md`, `images`, `terms_and_conditions_md` fields matching splitpayments pattern
- Tile image file exists at the path referenced by config.json
- README.md and LICENSE (MIT) files exist in extension root
- description.md file exists for extension manager
- JS toast notification fires when an arrangement transitions to "completed" (not on every refresh)
- Cutover verification test proves: debt update → status "completed" → subsequent payments skipped
- `min_lnbits_version` set to `"1.3.0"` (matches splitpayments; covers APIs we use)

## Proof Level

- This slice proves: final-assembly
- Real runtime required: no (contract tests sufficient; UAT deferred to milestone-level verification)
- Human/UAT required: yes (extension install from GitHub, dashboard visual check)

## Verification

- `python -m pytest tests/extensions/orangepiller/test_cutover.py -v` — all tests pass
- `python -c "import json; c=json.load(open('orangepiller/config.json')); assert 'version' in c; assert 'license' in c; assert 'description_md' in c; print('config.json OK')"` — passes
- `test -f orangepiller/static/image/orange-piller.png && echo "tile OK"` — passes
- `test -f orangepiller/README.md && test -f orangepiller/LICENSE && test -f orangepiller/description.md && echo "docs OK"` — passes
- `grep -q 'notify' orangepiller/static/js/index.js && echo "notification OK"` — toast code present
- `python -c "from lnbits.extensions.orangepiller.config import orangepiller_ext; print(orangepiller_ext)" 2>&1 | head -5` — extension config loads without error (failure: ImportError or missing field traceback)

## Observability / Diagnostics

- Runtime signals: Quasar toast notification on arrangement completion transition (client-side only)
- Inspection surfaces: config.json parseable by LNbits ExtensionConfig model; `SELECT status FROM orangepiller.arrangements` shows completion state
- Failure visibility: Missing tile image → broken image in extension manager; missing config fields → install failure
- Redaction constraints: none

## Integration Closure

- Upstream surfaces consumed: `crud.py` (update_arrangement_repaid with status transition), `tasks.py` (on_invoice_paid with skip logic), `index.js` (_mapArrangement, getArrangements), `index.html` (status chips)
- New wiring introduced in this slice: completion toast detection in JS, packaging files for extension manager
- What remains before the milestone is truly usable end-to-end: UAT on a running LNbits instance (milestone-level verification, not slice-scoped)

## Tasks

- [x] **T01: Complete extension packaging for GitHub install** `est:20m`
  - Why: R009 requires a standalone GitHub-installable extension. config.json is missing required fields, no tile image exists, no README/LICENSE/description.md.
  - Files: `orangepiller/config.json`, `orangepiller/README.md`, `orangepiller/LICENSE`, `orangepiller/description.md`, `orangepiller/static/image/orange-piller.png`
  - Do: Add `version`, `license`, `description_md`, `images`, `terms_and_conditions_md` to config.json following splitpayments pattern. Set `min_lnbits_version` to `"1.3.0"`. Update tile path. Create a minimal orange PNG tile image (can be a 1x1 placeholder or simple generated PNG). Write README.md with extension description, install instructions, usage overview. Write MIT LICENSE file. Write description.md for extension manager.
  - Verify: `python -c "import json; c=json.load(open('orangepiller/config.json')); assert all(k in c for k in ['version','license','description_md']); print('OK')"` and file existence checks
  - Done when: config.json has all required fields, tile image exists at referenced path, README.md + LICENSE + description.md present

- [x] **T02: Add completion toast notification and cutover verification test** `est:20m`
  - Why: R010 requires a visible notification when debt is fully repaid. R008 needs test proof that the cutover path works end-to-end (debt zero → status completed → skipped).
  - Files: `orangepiller/static/js/index.js`, `tests/extensions/orangepiller/test_cutover.py`
  - Do: In index.js, add completion detection to `getArrangements()` and `getMerchantArrangements()` — before overwriting the data array, compare old statuses with new statuses and fire `$q.notify({type:'positive', message:'...'})` for any arrangement that transitioned to "completed". Write test_cutover.py with tests: (1) atomic update transitions status to completed when repaid >= total, (2) on_invoice_paid skips completed arrangements, (3) exact payoff caps correctly and completes.
  - Verify: `python -m pytest tests/extensions/orangepiller/test_cutover.py -v` passes; `grep -q 'notify.*completed\|completed.*notify' orangepiller/static/js/index.js`
  - Done when: Tests pass proving cutover path; JS has transition-aware toast notification code

## Files Likely Touched

- `orangepiller/config.json`
- `orangepiller/README.md`
- `orangepiller/LICENSE`
- `orangepiller/description.md`
- `orangepiller/static/image/orange-piller.png`
- `orangepiller/static/js/index.js`
- `tests/extensions/orangepiller/test_cutover.py`
