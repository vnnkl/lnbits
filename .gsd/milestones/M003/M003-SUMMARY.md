---
id: M003
provides:
  - Fiat-denominated debt tracking with spot-rate conversion on each payment
  - Dual-path reroute engine (sat unchanged, fiat uses LNbits exchange rate service)
  - Migration m003_fiat_fields adding debt_currency, total_debt_fiat, repaid_fiat
  - Currency-aware onboarding form with dropdown and dynamic labels
  - Fiat-aware dashboard display on both orange piller and merchant tables
  - Graceful exchange rate failure handling (skip reroute, log warning)
key_decisions:
  - "Spot-rate conversion per payment via satoshis_amount_as_fiat / fiat_amount_as_satoshis"
  - "Exchange rate failure skips reroute — merchant keeps full payment"
  - "Fiat stored as float, rounded on display only"
  - "debt_currency='sat' sentinel preserves existing sat path unchanged"
  - "Single debt_amount form field mapped to sat or fiat in JS"
patterns_established:
  - Dual-path reroute with extracted _handle_fiat_reroute function
  - Fiat atomic SQL UPDATE with CASE cap mirroring sat pattern
  - Currency-aware display formatting in _mapArrangement()
observability_surfaces:
  - logger.info on fiat reroute with exchange rate, fiat amount, sat equivalent
  - logger.warning on exchange rate failure with currency and error
  - DB inspection: SELECT debt_currency, total_debt_fiat, repaid_fiat FROM orangepiller.arrangements
requirement_outcomes:
  - id: R012
    from_status: active
    to_status: validated
    proof: Fiat reroute engine converts at spot, caps at remaining fiat debt, completes when fiat debt reaches zero; 12 tests prove all paths; dashboard shows fiat amounts
duration: 35m
verification_result: passed
completed_at: 2026-03-16
---

# M003: Fiat-Denominated Debt Tracking

**Fiat-denominated debt tracking with spot-rate conversion, dual-path reroute engine, currency-aware onboarding and dashboard — 44/44 tests pass, verified on live Docker instance.**

## What Happened

**S01 (20m)** built the data and engine layer. Added `debt_currency`, `total_debt_fiat`, `repaid_fiat` to the Arrangement model with fiat-aware computed properties. The reroute engine branches on `debt_currency`: sat path unchanged, fiat path fetches spot rate via `satoshis_amount_as_fiat()`, applies reroute % in fiat space, caps at remaining fiat debt, converts back to sats, and transfers atomically. Exchange rate failures gracefully skip the reroute. 12 new tests cover happy path, cap, exact payoff, rate failure, rollback, and backward compat.

**S02 (15m)** wired the frontend. Currency select dropdown in the onboarding form with 10 common currencies plus free-text entry. Debt input label dynamically changes ("Total Debt (sats)" vs "Total Debt (EUR)"). Dashboard tables show formatted amounts ("100.00 EUR" or "50,000 sats") per row. Verified on Docker: both fiat and sat arrangements coexist correctly in the same table.

## Cross-Slice Verification

All 6 success criteria verified:
1. ✅ EUR arrangement created with €100 debt through onboarding form
2. ✅ Fiat reroute engine converts at spot, applies %, transfers sats (12 tests)
3. ✅ Fiat debt cap + completion (test_fiat_cap_at_remaining, test_fiat_exact_payoff_completes)
4. ✅ Sat arrangements backward-compatible (test_sat_arrangement_uses_sat_path, all 32 original tests)
5. ✅ Dashboard shows "100.00 EUR" / "0.00 EUR" for fiat, "50,000 sats" for sat
6. ✅ Exchange rate failure skips reroute (test_exchange_rate_failure_skips_reroute)

## Requirement Changes
- R012: active → validated — Fiat-denominated debt tracking delivered and proven

## Files Created/Modified
- `orangepiller/models.py` — 3 new Arrangement fields, 2 CreateArrangement fields, fiat-aware properties
- `orangepiller/migrations.py` — m003_fiat_fields migration
- `orangepiller/crud.py` — update_arrangement_repaid_fiat, rollback_arrangement_repaid_fiat
- `orangepiller/tasks.py` — fiat branch + _handle_fiat_reroute
- `orangepiller/views_api.py` — fiat validation + forgiveness
- `orangepiller/static/js/index.js` — currency-aware form + dashboard display
- `orangepiller/templates/orangepiller/index.html` — currency select + dynamic debt label
- `tests/extensions/orangepiller/test_fiat_reroute.py` — 12 fiat tests
