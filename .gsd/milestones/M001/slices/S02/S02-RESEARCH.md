# M001/S02 — Research

**Date:** 2026-03-16

## Summary

S02 implements the payment rerouting engine — the core mechanic of the Orange Piller extension. When a merchant receives a payment, the extension intercepts it via an invoice listener, calculates the reroute amount (percentage of payment capped at remaining debt), and performs an internal transfer to the orange piller's wallet.

The existing `splitpayments` extension provides a near-identical pattern: `register_invoice_listener` → queue → `on_invoice_paid` → `create_invoice` (on target wallet) → `pay_invoice` (from source wallet). The key differences for orangepiller are: (1) debt tracking with a cap, (2) status transition to "completed" when debt hits zero, (3) the re-entrant tag guard must use `"orangepiller"` instead of `"splitpayments"`, and (4) concurrency safety for the debt update.

The concurrency risk — identified in the roadmap as high — is partially mitigated by LNbits' `Database.lock` (`asyncio.Lock`) which serializes all DB operations on the extension's SQLite/Postgres connection. However, since the reroute logic spans multiple DB calls (read arrangement → calculate cap → update repaid), a race window exists between the read and update. The fix is to use `db.connect()` to hold the lock across the entire read-calculate-update sequence, or use a single atomic SQL UPDATE with a CASE expression that does the cap in SQL.

## Recommendation

**Use an atomic single-SQL-statement approach for the debt update.** Instead of read-then-update, do:

```sql
UPDATE orangepiller.arrangements
SET repaid_sats = CASE
    WHEN repaid_sats + :amount > total_debt_sats THEN total_debt_sats
    ELSE repaid_sats + :amount
END,
status = CASE
    WHEN repaid_sats + CASE
        WHEN repaid_sats + :amount > total_debt_sats THEN total_debt_sats - repaid_sats
        ELSE :amount
    END >= total_debt_sats THEN 'completed'
    ELSE status
END
WHERE id = :id AND status = 'active'
RETURNING *
```

This eliminates the race entirely — the cap and status transition happen atomically in one statement. The `WHERE status = 'active'` guard also prevents rerouting on already-completed arrangements.

For the payment interception, follow the splitpayments pattern exactly but add the debt cap logic. The overall flow:

1. `on_invoice_paid` receives payment
2. Skip if tagged `"orangepiller"` (prevent infinite loops)
3. Look up active arrangement by `payment.wallet_id`
4. Calculate: `reroute_sats = min(payment.sat * arrangement.reroute_percent // 100, arrangement.remaining_debt)`
5. If `reroute_sats <= 0`, skip
6. Atomically update debt (SQL above) — returns actual amount applied
7. `create_invoice` on orange piller wallet for `reroute_sats` sats, `internal=True`
8. `pay_invoice` from merchant wallet with `extra={"tag": "orangepiller"}`
9. Log the transfer

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Payment interception | `register_invoice_listener` + asyncio.Queue from `lnbits.tasks` | Battle-tested pattern used by splitpayments and core |
| Internal transfer | `create_invoice` + `pay_invoice` from `lnbits.core.services` | Handles all payment bookkeeping, balance updates, and internal routing |
| Task lifecycle | `create_permanent_unique_task` from `lnbits.tasks` | Auto-restarts on crash, deduplicates by name |
| Unique IDs | `urlsafe_short_hash` from `lnbits.helpers` | Already used in S01 CRUD |

## Existing Code and Patterns

- `/tmp/splitpayments/tasks.py` — **Primary reference.** `wait_for_paid_invoices` → `on_invoice_paid` pattern. Key detail: `payment.amount` is in **millisatoshis** (despite the field name), so splitpayments does `int(payment.amount * target.percent / 100)` for msat and `int(amount_msat / 1000)` for the `create_invoice` amount (which takes sats). Our debt is in sats, so we must convert.
- `/tmp/splitpayments/__init__.py` — Task wiring: `orangepiller_start()` calls `create_permanent_unique_task("ext_orangepiller", wait_for_paid_invoices)`. Already wired in our `__init__.py`.
- `orangepiller/tasks.py` — S01 skeleton already has the listener loop and tag guard. Needs: arrangement lookup, cap calculation, transfer logic, debt update.
- `orangepiller/crud.py` — `get_arrangement_by_merchant_wallet(wallet_id)` returns the active arrangement. `update_arrangement_repaid(arrangement_id, additional_sats)` does a simple `repaid_sats += sats` — **must be upgraded to atomic cap + status transition**.
- `lnbits/db.py` — `Database.connect()` acquires `self.lock` (asyncio.Lock), serializing all access. Each top-level method (`execute`, `fetchone`, etc.) calls `connect()` independently. To hold the lock across multiple operations, use `async with db.connect() as conn:` and call `conn.execute()` / `conn.fetchone()` directly.
- `lnbits/core/services/payments.py` — `create_invoice(wallet_id=..., amount=N, internal=True, memo=...)` creates an invoice in sats. `pay_invoice(wallet_id=..., payment_request=..., extra=...)` pays it.

## Constraints

- **`payment.amount` is in millisatoshis** — `payment.sat` property gives sats (`amount // 1000`). Debt tracking is in sats, so use `payment.sat` for calculations.
- **`create_invoice` amount parameter is in sats** (integer) — splitpayments converts from msat: `int(amount_msat / 1000)`.
- **Pydantic v1** — no `model_dump()`, use `.dict()`. Computed properties not serialized.
- **No new dependencies** — everything needed is in LNbits core.
- **SQLite and PostgreSQL compatibility** — SQL must work on both. `CASE WHEN` is standard SQL and works on both. Avoid `RETURNING *` if SQLite doesn't support it (SQLite 3.35+ does, but safer to do a separate SELECT after UPDATE).
- **asyncio.Lock on Database** — the ext DB lock is per-Database-instance. Since we use `Database("ext_orangepiller")`, our lock is separate from core's. Operations within our DB are serialized, but be aware that the `create_invoice`/`pay_invoice` calls go through core's DB — those are independent.
- **`internal=True` on create_invoice** — critical for same-instance transfers. Without it, LNbits would try to pay via the funding source (external Lightning node).

## Common Pitfalls

- **Infinite loop via re-entrant payments** — When the extension pays the orange piller via `pay_invoice`, that generates a new payment event. The listener will fire again. Must guard with `payment.extra.get("tag") == "orangepiller"` to skip rerouted payments. Splitpayments uses both `"tag"` and `"splitted"` checks.
- **Overpayment beyond debt ceiling** — Without atomic cap, two concurrent payments could each read `remaining_debt=100` and each reroute 100 sats, overpaying by 100. The atomic SQL UPDATE with CASE prevents this.
- **msat vs sat confusion** — `payment.amount` is msat, `payment.sat` is sats. `create_invoice(amount=...)` expects sats. Mixing these up would cause 1000x over/under-payment.
- **Reroute amount of 0 sats** — If the percentage calculation rounds down to 0 (e.g., 1% of a 50-sat payment = 0.5 → 0), skip the transfer entirely. `create_invoice` rejects amount=0.
- **RETURNING clause portability** — SQLite < 3.35 doesn't support `RETURNING`. Safer to do UPDATE then SELECT. The asyncio.Lock ensures no interleaving between them on the same Database instance.
- **Status check before rerouting** — Must check `arrangement.status == "active"` before rerouting. Also add `WHERE status = 'active'` in the UPDATE to prevent races where arrangement was completed between the check and the update.

## Open Risks

- **`update_arrangement_repaid` needs redesign** — The current S01 implementation does a simple `repaid_sats += sats` with no cap or status transition. S02 must either modify this function or create a new atomic version. Modifying is preferred since no other caller exists yet.
- **Payment failure after debt update** — If we update the debt first but `pay_invoice` fails, the debt is decremented but the orange piller didn't receive funds. Two options: (a) update debt only after successful payment (risk: concurrent payment in the gap), (b) update debt first, if payment fails, roll back debt. Option (a) is what splitpayments does — it fires and forgets via `asyncio.create_task`. For correctness, we should update debt first (holding the lock), then pay. If payment fails, reverse the debt increment.
- **Large reroute percentages with small payments** — 100% reroute on a 1-sat payment works fine. But floor division might lose a fraction of a sat on each payment. This is acceptable — sats are the smallest unit we track.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| LNbits | — | No specific skills found; LNbits is niche. Splitpayments reference is sufficient. |

## Sources

- splitpayments extension at `/tmp/splitpayments/` — exact payment interception and internal transfer pattern
- `lnbits/db.py` — Database class with asyncio.Lock serialization, Connection context manager
- `lnbits/core/services/payments.py` — `create_invoice` and `pay_invoice` signatures and internal transfer support
- `lnbits/tasks.py` — `register_invoice_listener` and `create_permanent_unique_task` APIs
- `lnbits/core/models/payments.py` — Payment model: `amount` is msat, `sat` property is `amount // 1000`
