# M003: Fiat-Denominated Debt Tracking

**Vision:** Orange pillers can denominate payback debt in any fiat currency. Each incoming Bitcoin payment is converted to fiat at the current spot rate, with the reroute percentage applied in fiat space. The orange piller recovers the exact fiat value they fronted, regardless of BTC price movements. Sat-denominated debts continue to work unchanged.

## Success Criteria

- Orange piller creates a EUR-denominated arrangement (e.g. €100) through the onboarding form and the debt is stored and displayed in EUR
- When the merchant receives a sat payment, the reroute engine converts the payment to EUR at the current spot rate, applies the reroute %, and transfers the equivalent sats back to the orange piller
- Fiat debt decrements correctly until it reaches €0.00, at which point rerouting stops automatically
- A sat-denominated arrangement created and completed through the same code path behaves identically to M001/M002 behavior
- Both dashboards display fiat amounts with the correct currency symbol and fiat progress bars for fiat-denominated arrangements
- If the exchange rate is unavailable, the payment is skipped (not lost) — the merchant keeps the full amount and a warning is logged

## Key Risks / Unknowns

- **Exchange rate failure during reroute** — `satoshis_amount_as_fiat()` raises `ValueError` when the rate is unavailable. If this happens mid-payment, the reroute must be cleanly skipped. LNbits caches rates for 30s, so brief outages are covered, but extended downtime means payments accumulate without rerouting.
- **Float precision drift** — Tracking fiat as a float risks cumulative rounding errors over many small payments. Need to verify that Python `float` precision is sufficient for realistic debt ranges (up to ~€10,000 with payments in fractional cents).

## Proof Strategy

- Exchange rate failure handling → retire in S01 by proving the fiat reroute path gracefully skips when `satoshis_amount_as_fiat` raises, with a test using a mocked failing rate provider
- Float precision → retire in S01 by proving that 1000 small fiat repayments sum correctly to the total debt without drift beyond 1 cent

## Verification Classes

- Contract verification: pytest unit tests with mocked exchange rates covering fiat reroute, cap logic, failure handling, backward compatibility
- Integration verification: live LNbits instance with exchange rate providers — create fiat arrangement, trigger payment, observe correct conversion and debt decrement
- Operational verification: dashboard displays correct fiat formatting; exchange rate API failure logs warning and skips cleanly
- UAT / human verification: onboarding form UX — currency selection, debt amount input, dashboard display

## Milestone Definition of Done

This milestone is complete only when all are true:

- Fiat reroute engine converts payments at spot rate, decrements fiat debt, and transfers correct sat amount
- Fiat debt cap logic prevents overpayment — final reroute is capped at remaining fiat debt
- Sat-denominated arrangements pass all existing M001/M002 tests unchanged
- Exchange rate failure is handled gracefully (skip, log, no data corruption)
- Both dashboards show fiat amounts with currency symbols for fiat arrangements, sats for sat arrangements
- Onboarding form allows selecting fiat currency and entering fiat debt amount
- All success criteria re-checked on live Docker instance
- Migration adds fiat columns without breaking existing data

## Requirement Coverage

- Covers: R012 (fiat-denominated debt tracking — primary deliverable)
- Extends: R002 (payback config now supports fiat denomination), R003 (reroute engine fiat branch), R004 (fiat cap logic), R005 (dashboard fiat display), R006 (merchant fiat display)
- Leaves for later: R011 (store map listing — unrelated)
- Orphan risks: none

## Slices

- [x] **S01: Fiat reroute engine and data model** `risk:high` `depends:[]`
  > After this: a fiat-denominated arrangement can be created via the API, and incoming payments are converted at spot rate and rerouted with fiat debt tracking — proven by unit tests with mocked exchange rates.

- [x] **S02: Dashboard fiat display and onboarding form** `risk:low` `depends:[S01]`
  > After this: the onboarding form allows selecting a fiat currency and entering a fiat debt amount; both dashboards display fiat debt, repaid amount, remaining balance, and progress with currency symbols; the full flow is verified on the live Docker instance.

## Boundary Map

### S01 → S02

Produces:
- `Arrangement` model with `debt_currency`, `total_debt_fiat`, `repaid_fiat` fields
- `CreateArrangement` model with `debt_currency` and `total_debt_fiat` fields (debt_currency defaults to "sat" for backward compat)
- `create_arrangement()` CRUD that stores fiat fields when debt_currency != "sat"
- `update_arrangement_repaid_fiat(id, fiat_amount)` CRUD with atomic SQL cap at `total_debt_fiat`
- `rollback_arrangement_repaid_fiat(id, fiat_amount)` CRUD for transfer failure rollback
- `on_invoice_paid()` dual-path: sat path unchanged, fiat path fetches rate → converts → reroutes → updates fiat debt
- Migration `m003_fiat_fields` adding `debt_currency`, `total_debt_fiat`, `repaid_fiat` columns
- Computed properties: `remaining_debt_fiat`, `progress_percent` aware of debt_currency
- All existing sat-denominated tests still pass

Consumes:
- nothing (extends existing interfaces)

### S02 consumes from S01:
- `Arrangement.debt_currency` to branch display logic (fiat vs sat)
- `Arrangement.total_debt_fiat`, `Arrangement.repaid_fiat` for fiat amounts
- `CreateArrangement.debt_currency`, `CreateArrangement.total_debt_fiat` for form submission
- Computed `remaining_debt_fiat` and `progress_percent` for display
