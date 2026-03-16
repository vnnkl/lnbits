---
estimated_steps: 5
estimated_files: 2
---

# T02: Fiat-aware dashboard display

**Slice:** S02 — Dashboard fiat display and onboarding form
**Milestone:** M003

## Description

Update both the orange piller and merchant dashboard tables to display fiat amounts with currency symbols for fiat-denominated arrangements, while showing sats for sat-denominated arrangements.

## Steps

1. Update `_mapArrangement()` in `index.js`: for fiat arrangements (`debt_currency !== 'sat'`), compute `remaining_debt` from `total_debt_fiat - repaid_fiat`, `progress_percent` from `repaid_fiat / total_debt_fiat * 100`. Add `debt_label` field with formatted amount (e.g. "€100.00" or "50,000 sats") for Total Debt, Repaid, and Remaining
2. Update column definitions: change labels from hardcoded "Total Debt (sats)" to dynamic. Use cell format functions or body-cell template slots that check `row.debt_currency` and display the appropriate formatted value with currency symbol
3. In the orange piller table body-cell slots for `total_debt_sats`, `repaid_sats`, `remaining_debt`: show fiat formatted values when `debt_currency !== 'sat'`, sat values when `debt_currency === 'sat'`. Use a helper method like `formatDebtAmount(row, field)` that returns the right string
4. Apply the same formatting to the merchant table columns
5. Ensure progress bar still works: `progress_percent` already computed correctly in `_mapArrangement()`, so the progress bar template needs no changes

## Must-Haves

- [ ] Fiat arrangements show amounts with currency symbol (e.g. "€100.00")
- [ ] Sat arrangements show amounts in sats (unchanged from M002)
- [ ] Progress bar works correctly for both fiat and sat arrangements
- [ ] Both orange piller and merchant tables are fiat-aware
- [ ] Column headers adapt or cell values self-describe the currency

## Verification

- Docker `localhost:5001`: create both EUR and sat arrangements, verify they display correctly side-by-side in the table
- Progress bars show correct fill for both types
- `pytest tests/extensions/orangepiller/ -v` — all tests pass

## Inputs

- `orangepiller/static/js/index.js` — current `_mapArrangement()`, column definitions, table templates
- `orangepiller/templates/orangepiller/index.html` — current table body-cell slots
- S01 boundary: `Arrangement` has `debt_currency`, `total_debt_fiat`, `repaid_fiat` fields

## Expected Output

- `orangepiller/static/js/index.js` — fiat-aware `_mapArrangement()` and formatting helpers
- `orangepiller/templates/orangepiller/index.html` — fiat-aware body-cell templates
