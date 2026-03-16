# S02: Dashboard fiat display and onboarding form

**Goal:** Update the onboarding form to support fiat currency selection and fiat debt amount input. Update both dashboards to display fiat amounts with currency symbols for fiat-denominated arrangements. Verify the full flow on the live Docker instance.
**Demo:** Open the Orange Piller page → click Onboard Merchant → select EUR as currency → enter €100 debt → submit → arrangement table shows "€100.00" in the Total Debt column → simulate a payment → dashboard shows updated fiat progress with € symbol.

## Must-Haves

- Onboarding form: when currency is not "sat", the debt input field label changes from "Total Debt (sats)" to "Total Debt (EUR)" (or whatever currency is selected) and the value is stored as `total_debt_fiat`
- When currency is "sat", the form and API behavior is identical to M002 (backward compat)
- Orange piller dashboard: fiat arrangements show debt, repaid, and remaining in fiat with currency symbol (e.g. "€100.00", "€23.45"); sat arrangements show sats as before
- Merchant dashboard: same fiat-aware display
- Progress bar works correctly for fiat arrangements (based on `repaid_fiat / total_debt_fiat`)
- Column headers are currency-aware (e.g. "Total Debt (EUR)" not "Total Debt (sats)")
- Full flow verified on Docker instance: create fiat arrangement → see fiat values on dashboard

## Verification

- `pytest tests/extensions/orangepiller/ -v` — all tests pass
- Visual verification on Docker at `localhost:5001`: create a fiat arrangement, see correct display
- Sat arrangement creation still works identically to before

## Tasks

- [ ] **T01: Currency-aware onboarding form** `est:20m`
  - Why: Users need to be able to create fiat-denominated arrangements through the UI
  - Files: `orangepiller/templates/orangepiller/index.html`, `orangepiller/static/js/index.js`
  - Do: In the onboard dialog, make the debt amount field reactive to the currency select. When currency is "sat": label "Total Debt (sats)", bind to `onboardForm.total_debt_sats`. When currency is anything else: label "Total Debt ({currency})", bind to `onboardForm.total_debt_fiat`. Update `createArrangement()` JS method to send `total_debt_fiat` and `debt_currency` when fiat, or `total_debt_sats` when sat. Add `debt_currency` and `total_debt_fiat` to the `onboardForm` data object. Populate currency select with common options (sat, USD, EUR, GBP, CHF, JPY) plus free-text input for other currencies.
  - Verify: Open onboard dialog → select EUR → field label changes → submit creates fiat arrangement; select sat → field label shows sats → submit creates sat arrangement
  - Done when: Both fiat and sat arrangements can be created from the UI form

- [ ] **T02: Fiat-aware dashboard display** `est:25m`
  - Why: The dashboard needs to show fiat amounts for fiat arrangements and sats for sat arrangements
  - Files: `orangepiller/static/js/index.js`, `orangepiller/templates/orangepiller/index.html`
  - Do: Update `_mapArrangement()` to compute `remaining_debt` and `progress_percent` based on `debt_currency`. For fiat: `remaining_debt = total_debt_fiat - repaid_fiat`, `progress_percent = repaid_fiat / total_debt_fiat * 100`. For sat: unchanged. Add a `debt_display` computed field that formats the amount with currency symbol (e.g. "€100.00" or "50,000 sats"). Update column definitions to be dynamic or use cell formatters that check `debt_currency`. Update both orange piller and merchant table columns: Total Debt, Repaid, Remaining columns should show fiat or sat amounts depending on the row's `debt_currency`. Progress bar should use the correct basis. Verify the poster page still works for fiat arrangements.
  - Verify: Docker `localhost:5001` — create EUR and sat arrangements side by side, both display correctly with appropriate formatting
  - Done when: Dashboard correctly displays fiat amounts with symbols for fiat arrangements, sats for sat arrangements, and progress bars work for both

- [ ] **T03: Live Docker verification and polish** `est:15m`
  - Why: Prove the full stack works end-to-end on a real running instance
  - Files: none (verification only, minor fixes if needed)
  - Do: On Docker `localhost:5001`: (1) Create a new EUR arrangement via the onboarding form, (2) verify the arrangement table shows EUR amounts, (3) verify the merchant dashboard shows EUR values, (4) check that existing sat arrangements still display correctly, (5) verify the poster page still works. Fix any visual issues found during verification.
  - Verify: Screenshots of both dashboards showing fiat and sat arrangements side by side; all tests still pass
  - Done when: Full visual verification passes on Docker instance; all tests pass; both fiat and sat flows work correctly through the UI

## Files Likely Touched

- `orangepiller/static/js/index.js`
- `orangepiller/templates/orangepiller/index.html`
