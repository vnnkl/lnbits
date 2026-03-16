# S01: Fiat reroute engine and data model

**Goal:** Add fiat-denominated debt tracking to the data model, migration, and reroute engine. The fiat path converts incoming sat payments to fiat at spot rate, applies reroute % in fiat space, transfers the equivalent sats, and decrements fiat debt atomically. Sat path is unchanged.
**Demo:** Create a EUR arrangement via API → simulate a sat payment with mocked exchange rate → see fiat debt decremented correctly → debt reaches zero → rerouting stops. All 32 existing tests still pass.

## Must-Haves

- `Arrangement` model has `debt_currency`, `total_debt_fiat`, `repaid_fiat` fields
- `CreateArrangement` accepts `debt_currency` and `total_debt_fiat`; defaults to `debt_currency="sat"` for backward compat
- Migration `m003_fiat_fields` adds 3 nullable columns; existing rows unaffected
- `on_invoice_paid` fiat branch: fetches spot rate → converts payment sats to fiat → applies reroute % → caps at remaining fiat debt → converts fiat reroute back to sats → transfers → updates fiat debt
- Fiat cap logic: final payment reroutes only the remaining fiat debt equivalent, not more
- Exchange rate failure: `on_invoice_paid` catches the exception, logs a warning, skips the reroute (merchant keeps full payment)
- Atomic fiat debt update prevents concurrent overpayment (same pattern as sat path)
- All 32 existing tests pass unchanged (sat path untouched)
- New tests cover: fiat reroute happy path, fiat cap at remaining debt, fiat exact payoff + completion, exchange rate failure skip, backward compat with sat arrangements

## Proof Level

- This slice proves: contract (mocked exchange rates, no live API calls in tests)
- Real runtime required: no (tested with mocks)
- Human/UAT required: no

## Verification

- `pytest tests/extensions/orangepiller/ -v` — all existing 32 tests pass
- `pytest tests/extensions/orangepiller/test_fiat_reroute.py -v` — new fiat-specific tests pass
- Manual spot-check: create a fiat arrangement via the test helper, verify `debt_currency`, `total_debt_fiat`, `repaid_fiat` fields are populated

## Observability / Diagnostics

- Runtime signals: `logger.info` on fiat reroute with exchange rate used, fiat amount, sat equivalent; `logger.warning` on exchange rate failure with currency and error
- Inspection surfaces: `SELECT debt_currency, total_debt_fiat, repaid_fiat FROM orangepiller.arrangements` for fiat state
- Failure visibility: exchange rate failure logged with arrangement ID, currency, and exception message; reroute skipped cleanly

## Integration Closure

- Upstream surfaces consumed: `lnbits.utils.exchange_rates.satoshis_amount_as_fiat`, `lnbits.utils.exchange_rates.fiat_amount_as_satoshis`
- New wiring introduced: fiat branch in `on_invoice_paid`, fiat CRUD functions, fiat model fields
- What remains before the milestone is truly usable end-to-end: dashboard fiat display (S02)

## Tasks

- [ ] **T01: Fiat data model, migration, and CRUD** `est:25m`
  - Why: Foundation — all fiat tracking depends on having the fields, migration, and CRUD operations
  - Files: `orangepiller/models.py`, `orangepiller/migrations.py`, `orangepiller/crud.py`, `orangepiller/views_api.py`
  - Do: Add `debt_currency` (str, default "sat"), `total_debt_fiat` (Optional[float]), `repaid_fiat` (float, default 0) to `Arrangement`. Add `debt_currency` and `total_debt_fiat` to `CreateArrangement`. Write `m003_fiat_fields` migration (3 ALTER TABLE ADD COLUMN). Add `update_arrangement_repaid_fiat(id, fiat_amount)` with atomic SQL cap at `total_debt_fiat` and status transition. Add `rollback_arrangement_repaid_fiat(id, fiat_amount)`. Update `create_arrangement()` to store fiat fields. Add computed `remaining_debt_fiat` property. Make `progress_percent` aware of `debt_currency`. Update POST handler to accept fiat fields and set `total_debt_sats=0` when `debt_currency != "sat"`.
  - Verify: `pytest tests/extensions/orangepiller/ -v` — all 32 existing tests still pass; manual import check of new CRUD functions
  - Done when: Arrangement model has all fiat fields, migration exists, CRUD fiat functions work, POST endpoint accepts fiat arrangements

- [ ] **T02: Fiat reroute engine path** `est:25m`
  - Why: The core mechanic — without this, fiat debt never gets repaid
  - Files: `orangepiller/tasks.py`
  - Do: In `on_invoice_paid`, after the status check, branch on `arrangement.debt_currency`. If "sat", run existing path unchanged. If fiat: call `satoshis_amount_as_fiat(payment.sat, arrangement.debt_currency)` to get fiat value of payment. Apply `reroute_percent` to get fiat reroute amount. Cap at `arrangement.remaining_debt_fiat`. Convert fiat reroute amount back to sats via `fiat_amount_as_satoshis`. Call `update_arrangement_repaid_fiat` atomically. Transfer sats via `create_invoice` + `pay_invoice`. Rollback fiat on transfer failure. Wrap exchange rate call in try/except ValueError — on failure, log warning and return (skip reroute). Log the exchange rate, fiat amount, and sat equivalent on success.
  - Verify: `pytest tests/extensions/orangepiller/test_fiat_reroute.py -v`
  - Done when: Fiat reroute path converts, transfers, and decrements correctly; exchange rate failure skips cleanly

- [ ] **T03: Fiat reroute tests** `est:20m`
  - Why: Prove the fiat path works correctly under all edge cases
  - Files: `tests/extensions/orangepiller/test_fiat_reroute.py`
  - Do: Write tests with mocked `satoshis_amount_as_fiat` and `fiat_amount_as_satoshis`: (1) fiat reroute happy path — 1000 sat payment at mocked rate → correct fiat decrement and sat transfer, (2) fiat cap at remaining debt — payment fiat-equivalent exceeds remaining → capped, (3) fiat exact payoff → debt reaches zero → status "completed", (4) exchange rate failure → ValueError raised → reroute skipped, merchant keeps payment, (5) sat arrangement backward compat → existing sat path unchanged when debt_currency="sat", (6) fiat precision — simulate 50 small payments that sum to the total debt, verify repaid_fiat matches total_debt_fiat exactly
  - Verify: `pytest tests/extensions/orangepiller/ -v` — all tests pass (32 existing + new fiat tests)
  - Done when: All fiat edge cases covered, all 32 existing tests still pass, test count is 38+

## Files Likely Touched

- `orangepiller/models.py`
- `orangepiller/migrations.py`
- `orangepiller/crud.py`
- `orangepiller/tasks.py`
- `orangepiller/views_api.py`
- `tests/extensions/orangepiller/test_fiat_reroute.py`
