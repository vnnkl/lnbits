---
estimated_steps: 5
estimated_files: 1
---

# T02: Fiat reroute engine path

**Slice:** S01 — Fiat reroute engine and data model
**Milestone:** M003

## Description

Add a fiat branch to the `on_invoice_paid` handler in tasks.py. When the arrangement's `debt_currency` is not "sat", the handler converts the incoming payment to fiat at spot rate, applies the reroute percentage in fiat, caps at remaining fiat debt, converts back to sats for the actual transfer, and updates the fiat debt atomically.

## Steps

1. Import `satoshis_amount_as_fiat` and `fiat_amount_as_satoshis` from `lnbits.utils.exchange_rates`
2. After the `arrangement.status != "active"` check, branch on `arrangement.debt_currency != "sat"` → call a new `_handle_fiat_reroute(payment, arrangement)` async function
3. In `_handle_fiat_reroute`: wrap the exchange rate call in try/except ValueError. On failure, log warning with arrangement ID and currency, and return (skip reroute — merchant keeps full payment)
4. On success: compute `fiat_payment_value = satoshis_amount_as_fiat(payment.sat, arrangement.debt_currency)`. Compute `fiat_reroute = fiat_payment_value * arrangement.reroute_percent / 100`. Cap: `fiat_reroute = min(fiat_reroute, arrangement.remaining_debt_fiat)`. Convert back: `reroute_sats = fiat_amount_as_satoshis(fiat_reroute, arrangement.debt_currency)`. If `reroute_sats <= 0`, return
5. Call `update_arrangement_repaid_fiat(arrangement.id, fiat_reroute)`, then `create_invoice` + `pay_invoice` for the sat transfer. On transfer failure, call `rollback_arrangement_repaid_fiat`. Log success with exchange rate, fiat amount, and sat equivalent

## Must-Haves

- [ ] Fiat branch activates when `debt_currency != "sat"`
- [ ] Exchange rate fetched via `satoshis_amount_as_fiat` (uses LNbits cached providers)
- [ ] Reroute % applied to fiat-equivalent of payment, not raw sats
- [ ] Fiat reroute capped at `remaining_debt_fiat`
- [ ] Actual sat transfer amount is the fiat reroute converted back to sats at same rate call
- [ ] Exchange rate failure → reroute skipped, warning logged, no data corruption
- [ ] Transfer failure → fiat debt rolled back via `rollback_arrangement_repaid_fiat`
- [ ] Success logged with rate, fiat amount, sat amount, arrangement state

## Verification

- Code review: `on_invoice_paid` has clear sat/fiat branch
- `from orangepiller.tasks import on_invoice_paid` succeeds
- Ready for test coverage in T03

## Inputs

- `orangepiller/tasks.py` — current sat-only reroute engine
- `orangepiller/crud.py` — T01's `update_arrangement_repaid_fiat` and `rollback_arrangement_repaid_fiat`
- `lnbits/utils/exchange_rates.py` — `satoshis_amount_as_fiat`, `fiat_amount_as_satoshis` (raises ValueError on failure)

## Expected Output

- `orangepiller/tasks.py` — fiat branch in `on_invoice_paid`, new `_handle_fiat_reroute` function
