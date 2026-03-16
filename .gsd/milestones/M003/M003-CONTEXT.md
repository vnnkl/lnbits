# M003: Fiat-Denominated Debt Tracking — Context

**Gathered:** 2026-03-16
**Status:** Queued — pending auto-mode execution

## Project Description

Add fiat-denominated debt to the Orange Piller extension. When the orange piller pays a merchant cash (e.g. €100), the debt is tracked in that fiat currency. Each incoming Bitcoin payment to the merchant is converted to fiat at the current spot rate, the reroute percentage is applied to the fiat-equivalent, and that fiat amount is subtracted from the debt. The actual sat transfer is whatever those fiat cents are worth at the same spot rate. Existing sat-denominated debts continue to work unchanged.

## Why This Milestone

The current model tracks debt in sats. But the orange piller pays the merchant in fiat — if Bitcoin's price rises after the arrangement is created, the merchant repays much more fiat-equivalent value than they received. If it drops, the orange piller takes a loss. Fiat-denominated debt makes the economic contract match reality: the orange piller gave €100 cash and gets back €100 worth of Bitcoin, regardless of price movements.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Create an arrangement with a fiat debt amount and currency (e.g. 100 EUR, 150 USD) instead of a sat amount
- See the debt, repaid amount, and remaining balance displayed in the fiat currency on both dashboards
- See each rerouted payment's fiat-equivalent value in the arrangement's progress
- Still create sat-denominated arrangements exactly as before (backward-compatible)
- See the exchange rate used for each conversion (audit trail)

### Entry point / environment

- Entry point: LNbits web UI → Orange Piller extension page (onboarding form currency selector)
- Environment: LNbits instance with exchange rate providers configured (default providers work out of the box)
- Live dependencies involved: LNbits exchange rate service (`lnbits.utils.exchange_rates`), external price API providers (configured in LNbits settings)

## Completion Class

- Contract complete means: Migration adds fiat columns, model supports both denomination modes, reroute engine converts at spot rate, tests verify fiat flow end-to-end with mocked exchange rates
- Integration complete means: Fiat arrangement on a running LNbits instance correctly converts a real payment using the live exchange rate, decrements fiat debt, and transfers the right number of sats
- Operational complete means: Dashboard displays fiat amounts with currency symbols, progress bars track fiat debt, and the system handles exchange rate API failures gracefully

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- End-to-end: create a EUR arrangement → merchant receives sat payment → payment converted to EUR at spot → reroute % applied to EUR amount → sat transfer executed → fiat debt decremented → debt reaches zero → rerouting stops
- Backward-compatible: existing sat arrangement continues to work identically (no behavioral change)
- Exchange rate failure: if the price API is unavailable, the reroute is deferred (not lost, not wrong) — payment stays in merchant wallet until next successful conversion

## Risks and Unknowns

- **Exchange rate availability** — `btc_price(currency)` calls external APIs. If all providers are down, we can't convert. Need a strategy: skip this payment (defer), use cached rate, or block. Deferring is safest but means the merchant keeps the full payment temporarily.
- **Precision and rounding** — Fiat amounts have 2 decimal places, sats are integers. Converting back and forth introduces rounding. Need to decide: round in merchant's favor (underpay orange piller by fractions of a cent) or track sub-cent precision internally.
- **Migration for existing arrangements** — Existing rows have `total_debt_sats` and `repaid_sats` in sats. New rows will have fiat equivalents. Need to handle the schema cleanly without breaking existing data. The `debt_currency` field determines which columns are authoritative.
- **Atomic consistency** — The spot rate must be fetched once per payment and used for both the fiat debt decrement and the sat transfer amount. If the rate changes between those two operations, the accounting breaks.

## Existing Codebase / Prior Art

- `lnbits/utils/exchange_rates.py` — `btc_price(currency)`, `fiat_amount_as_satoshis(amount, currency)`, `satoshis_amount_as_fiat(amount, currency)`, `get_fiat_rate_satoshis(currency)`. Cached, multi-provider with outlier filtering. This is the conversion engine.
- `orangepiller/tasks.py` — Current reroute engine. Branches on `arrangement.status`, calculates `reroute_sats`, calls atomic update + internal transfer. This is what needs a fiat branch.
- `orangepiller/models.py` — `Arrangement` with `total_debt_sats`, `repaid_sats`, computed `remaining_debt`, `progress_percent`. Needs fiat equivalents.
- `orangepiller/crud.py` — `update_arrangement_repaid(id, sats)` with atomic SQL. Needs a fiat variant or dual-mode update.
- `orangepiller/static/js/index.js` — Dashboard JS computing `remaining_debt` and `progress_percent` client-side. Needs to branch on currency.
- `orangepiller/templates/orangepiller/index.html` — Onboarding form already has a `currency` field (used for TPoS). This field could drive debt denomination too.
- TPoS extension — already handles fiat currencies with `exchange_rate` field on payments. Proves the pattern works in the LNbits ecosystem.

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R012 — Currently "out-of-scope" with note "User chose sats-denominated tracking." This milestone directly promotes R012 to active and delivers it.
- R002 — Currently validated for sat-denominated debt. This milestone extends it to support fiat denomination. The existing sat behavior must remain intact.
- R003 — Payment rerouting engine. The core reroute path needs a fiat conversion branch.
- R004 — Exact debt tracking with cap. Fiat cap logic mirrors the sat cap but in fiat space.
- R005 — Dashboard display. Must show fiat amounts and currency symbols.
- R006 — Merchant transparency. Merchant sees fiat debt and progress in their currency.

## Scope

### In Scope

- New model fields: `debt_currency` (e.g. "EUR", "USD", or "sat"), `total_debt_fiat` (float), `repaid_fiat` (float)
- Migration adding fiat columns to arrangements table (nullable, existing rows unaffected)
- Reroute engine fiat branch: fetch spot rate → convert payment to fiat → apply reroute % in fiat → convert reroute fiat back to sats → transfer sats → decrement fiat debt
- Atomic fiat debt update in SQL (cap `repaid_fiat` at `total_debt_fiat`, status transition)
- Onboarding form: debt amount input adapts label based on currency (sats vs fiat amount)
- Dashboard: fiat amounts with currency symbol, fiat progress bars, fiat remaining
- Merchant dashboard: same fiat display
- Exchange rate logged per reroute for auditability
- Graceful handling when exchange rate is unavailable (skip payment, log warning)
- Backward compatibility: `debt_currency = "sat"` uses existing sat-only path unchanged

### Out of Scope / Non-Goals

- Historical exchange rate charts or rate history UI
- Locked-rate arrangements (rate always spot at payment time)
- Multi-currency debt (one arrangement = one currency)
- Fiat payment acceptance (Stripe/PayPal) — this is about denomination, not payment rails
- Modifying the TPoS extension

## Technical Constraints

- Pydantic v1 (1.10.x) — no `@computed_field`
- SQLAlchemy 1.4 async
- No new Python dependencies (exchange_rates module is already in LNbits core)
- Float precision for fiat — use Python `round(x, 2)` for display, but track full precision internally to avoid cumulative rounding errors
- Exchange rate calls are async and may fail — must not block or crash the reroute handler
- Must work with both SQLite and PostgreSQL

## Integration Points

- `lnbits.utils.exchange_rates` — `satoshis_amount_as_fiat()` and `fiat_amount_as_satoshis()` for bidirectional conversion
- LNbits exchange rate provider configuration — determines which price APIs are used
- Existing orangepiller reroute engine — the fiat branch runs alongside the sat branch, selected by `debt_currency`
- Dashboard JS — needs currency-aware formatting and progress computation

## Open Questions

- **Rounding strategy** — Should sub-cent remainders accumulate internally and only round on display? Or round each payment individually? Accumulating is more accurate but adds complexity.
- **Exchange rate failure policy** — Skip the reroute entirely (safest, merchant keeps full payment temporarily) or use the last cached rate? LNbits caches rates for `lnbits_exchange_rate_cache_seconds` — a recent cache miss might still have a usable cached value.
- **Debt input UX** — Should the onboarding form show a single "Debt Amount" field that changes its label/unit based on the currency dropdown? Or separate fields for sat debt vs fiat debt?
