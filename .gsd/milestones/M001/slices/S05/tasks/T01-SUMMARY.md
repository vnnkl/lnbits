---
id: T01
parent: S05
milestone: M001
provides:
  - Complete extension packaging artifacts for GitHub-installable extension
key_files:
  - orangepiller/config.json
  - orangepiller/static/image/orange-piller.png
  - orangepiller/README.md
  - orangepiller/LICENSE
  - orangepiller/description.md
key_decisions:
  - Used empty images array (no screenshots yet) — can be populated when extension has UI screenshots
  - Generated a solid-orange 256x256 PNG as tile placeholder — replace with proper branding later
patterns_established:
  - Extension packaging follows splitpayments reference pattern (config.json fields, file layout)
observability_surfaces:
  - config.json parseable by LNbits ExtensionConfig model; missing fields cause install failure with validation error
duration: 8m
verification_result: passed
completed_at: 2026-03-16
blocker_discovered: false
---

# T01: Complete extension packaging for GitHub install

**Added all required extension manager fields to config.json, created tile image, README, LICENSE, and description.md**

## What Happened

Updated `orangepiller/config.json` with all fields required by the LNbits extension manager: `version` (0.1.0), `license` (MIT), `description_md`, `images`, `terms_and_conditions_md`, and updated `min_lnbits_version` to 1.3.0 and `tile` path to the new image location. Generated a 256x256 solid-orange PNG tile image using pure Python (no external dependencies). Wrote README.md with extension description, features, install instructions, and usage guide. Added MIT LICENSE file and description.md for the extension manager gallery.

## Verification

- `python -c "import json; c=json.load(open('orangepiller/config.json')); assert all(k in c for k in ['version','license','description_md','images','terms_and_conditions_md','min_lnbits_version']); assert c['min_lnbits_version']=='1.3.0'; print('OK')"` → **PASS**
- `test -f orangepiller/static/image/orange-piller.png` → **PASS** (tile exists, 852 bytes)
- `test -f orangepiller/README.md && test -f orangepiller/LICENSE && test -f orangepiller/description.md` → **PASS**

### Slice-level verification status (4/5 pass):
- ✅ config.json OK
- ✅ tile OK
- ✅ docs OK
- ✅ notification OK (pre-existing)
- ⬜ test_cutover.py — T02 scope

## Diagnostics

- Verify config validity: `python -c "import json; json.load(open('orangepiller/config.json'))"`
- Verify tile renders: check `orangepiller/static/image/orange-piller.png` exists and is valid PNG
- Missing config fields → LNbits ExtensionConfig validation error on install attempt

## Deviations

None.

## Known Issues

- `images` array is empty — no UI screenshots available yet. Populate when extension has finalized UI.
- Tile image is a solid orange placeholder — replace with proper branded artwork before public release.

## Files Created/Modified

- `orangepiller/config.json` — added version, license, description_md, images, terms_and_conditions_md, updated min_lnbits_version and tile path
- `orangepiller/static/image/orange-piller.png` — 256x256 solid-orange PNG tile image (generated)
- `orangepiller/README.md` — extension documentation with features, install, and usage sections
- `orangepiller/LICENSE` — MIT license
- `orangepiller/description.md` — short description for extension manager gallery
