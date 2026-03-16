---
estimated_steps: 5
estimated_files: 2
---

# T01: Currency-aware onboarding form

**Slice:** S02 — Dashboard fiat display and onboarding form
**Milestone:** M003

## Description

Update the onboarding dialog so the debt input field adapts to the selected currency. When "sat" is selected, it works as before. When a fiat currency is selected, the field label and API payload switch to fiat denomination.

## Steps

1. In `index.js`, add `total_debt_fiat: null` and `debt_currency: 'sat'` to the `onboardForm` data object
2. Update the onboard dialog in `index.html`: replace the fixed "Total Debt (sats)" input with a reactive field. Use `:label` bound to a computed expression: if `onboardForm.currency === 'sat'` → "Total Debt (sats) *", else → `"Total Debt (" + onboardForm.currency + ") *"`. Bind the `v-model` to `onboardForm.total_debt_sats` when sat, `onboardForm.total_debt_fiat` when fiat (use a shared field or conditional v-model)
3. Simplify: use a single `onboardForm.debt_amount` field, and in `createArrangement()` map it to either `total_debt_sats` or `total_debt_fiat` based on `onboardForm.currency`
4. Update `createArrangement()` method: when currency is "sat", send `total_debt_sats` and `debt_currency: "sat"` (backward compat). When fiat, send `total_debt_fiat`, `debt_currency`, and `total_debt_sats: 0`
5. Populate the currency field as a Quasar select with common options: sat, USD, EUR, GBP, CHF — and allow free-text entry for other currencies via `use-input` and `new-value-mode`

## Must-Haves

- [ ] Debt input label changes dynamically based on selected currency
- [ ] Sat arrangements created with `total_debt_sats` (backward compat)
- [ ] Fiat arrangements created with `total_debt_fiat` and `debt_currency`
- [ ] Currency select allows common currencies and free-text entry

## Verification

- Open onboard dialog on Docker → select EUR → label says "Total Debt (EUR)" → submit creates fiat arrangement
- Select sat → label says "Total Debt (sats)" → submit creates sat arrangement
- `pytest tests/extensions/orangepiller/ -v` — all tests pass

## Inputs

- `orangepiller/static/js/index.js` — current `onboardForm` and `createArrangement()` method
- `orangepiller/templates/orangepiller/index.html` — current onboard dialog markup
- S01 boundary: `CreateArrangement` accepts `debt_currency` and `total_debt_fiat`

## Expected Output

- `orangepiller/static/js/index.js` — updated form data and submit logic
- `orangepiller/templates/orangepiller/index.html` — reactive debt input in onboard dialog
