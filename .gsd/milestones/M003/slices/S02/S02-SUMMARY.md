---
id: S02
milestone: M003
provides:
  - Currency-aware onboarding form (dropdown with common currencies + free-text)
  - Debt input label dynamically changes based on selected currency
  - createArrangement() maps to total_debt_sats or total_debt_fiat
  - Fiat-aware dashboard display with currency symbols in both tables
  - _mapArrangement() computes fiat or sat display values based on debt_currency
key_files:
  - orangepiller/static/js/index.js
  - orangepiller/templates/orangepiller/index.html
key_decisions:
  - "Single debt_amount field mapped to sat or fiat in JS submit handler"
  - "Currency select moved from TPoS section to Payback Settings (drives both debt and TPoS)"
  - "Display strings computed in _mapArrangement() not column definitions"
drill_down_paths:
  - .gsd/milestones/M003/slices/S02/tasks/T01-PLAN.md
  - .gsd/milestones/M003/slices/S02/tasks/T02-PLAN.md
  - .gsd/milestones/M003/slices/S02/tasks/T03-PLAN.md
duration: 15m
verification_result: pass
completed_at: 2026-03-16
---

# S02: Dashboard fiat display and onboarding form

**Currency-aware onboarding form with dropdown and dynamic labels, plus fiat-aware dashboard showing EUR/USD amounts alongside sats — verified on live Docker instance.**

## What Happened

**T01** updated the onboarding dialog: currency moved from TPoS settings to Payback Settings as a `q-select` dropdown with 10 common currencies (sat, USD, EUR, GBP, CHF, JPY, CAD, AUD, BRL, MXN) plus free-text entry. A single `debt_amount` field adapts its label ("Total Debt (sats)" vs "Total Debt (EUR)") and the JS submit handler maps it to `total_debt_sats` or `total_debt_fiat + debt_currency` based on selection.

**T02** made both dashboards fiat-aware. `_mapArrangement()` now computes `debt_display`, `repaid_display`, and `remaining_display` as formatted strings (e.g. "100.00 EUR" or "50,000 sats"). Column definitions use these display fields instead of raw numbers. Column headers changed from "Total Debt (sats)" to "Total Debt" — each cell self-describes its currency.

**T03** verified on Docker at `localhost:5001`: created a EUR arrangement ("Euro Test Café", €100, 50% reroute), confirmed it appears in the table with "100.00 EUR" / "0.00 EUR" alongside existing sat arrangements showing "100,000 sats". Both types coexist correctly.

## Deviations
None.

## Files Created/Modified
- `orangepiller/static/js/index.js` — onboardForm, createArrangement(), _mapArrangement(), column definitions
- `orangepiller/templates/orangepiller/index.html` — onboard dialog: currency select + dynamic debt label
