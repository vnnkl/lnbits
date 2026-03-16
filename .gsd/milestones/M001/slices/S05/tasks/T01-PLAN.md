---
estimated_steps: 6
estimated_files: 5
---

# T01: Complete extension packaging for GitHub install

**Slice:** S05 — Clean cutover, notifications & packaging
**Milestone:** M001

## Description

The extension is missing several fields in config.json required by the LNbits extension manager (`version`, `license`, `description_md`, `images`, `terms_and_conditions_md`), has no tile image (config.json references a non-existent file), and lacks README.md, LICENSE, and description.md files. This task completes all packaging artifacts following the splitpayments extension as reference, making the extension installable from a GitHub manifest.

## Steps

1. Update `orangepiller/config.json` — add `version: "0.1.0"`, `license: "MIT"`, `description_md` URL, `images` array, `terms_and_conditions_md` URL, update `min_lnbits_version` to `"1.3.0"`, update `tile` path to `/orangepiller/static/image/orange-piller.png`
2. Create `orangepiller/static/image/` directory and generate a minimal PNG tile image (use Python to create a simple orange-colored PNG)
3. Write `orangepiller/README.md` with extension name, description, features, install instructions, and usage overview
4. Write `orangepiler/LICENSE` with MIT license text
5. Write `orangepiller/description.md` with a short description for the extension manager
6. Verify config.json parses correctly and all referenced files exist

## Must-Haves

- [ ] config.json has `version`, `license`, `description_md`, `images`, `terms_and_conditions_md` fields
- [ ] `min_lnbits_version` is `"1.3.0"`
- [ ] Tile image exists at the path referenced in config.json
- [ ] README.md, LICENSE, description.md exist in extension root

## Verification

- `python -c "import json; c=json.load(open('orangepiller/config.json')); assert all(k in c for k in ['version','license','description_md','images','terms_and_conditions_md','min_lnbits_version']); assert c['min_lnbits_version']=='1.3.0'; print('OK')"`
- `test -f orangepiller/static/image/orange-piller.png && echo "tile exists"`
- `test -f orangepiller/README.md && test -f orangepiller/LICENSE && test -f orangepiller/description.md && echo "docs exist"`

## Observability Impact

- **Signals changed:** config.json becomes parseable by LNbits ExtensionConfig model; tile image renders in extension manager UI
- **Inspection:** `python -c "import json; json.load(open('orangepiller/config.json'))"` verifies config validity; `test -f orangepiller/static/image/orange-piller.png` verifies tile
- **Failure visibility:** Missing/malformed config.json → extension install fails with ExtensionConfig validation error; missing tile → broken image in extension manager gallery; missing LICENSE → GitHub compliance warning

## Inputs

- `orangepiller/config.json` — current config missing packaging fields
- `/tmp/splitpayments/config.json` — reference for complete config structure
- `/tmp/splitpayments/README.md`, `/tmp/splitpayments/description.md`, `/tmp/splitpayments/LICENSE` — reference formats

## Expected Output

- `orangepiller/config.json` — complete with all extension manager fields
- `orangepiller/static/image/orange-piller.png` — tile image for extension manager
- `orangepiller/README.md` — extension documentation
- `orangepiller/LICENSE` — MIT license
- `orangepiller/description.md` — extension manager description
