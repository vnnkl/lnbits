---
estimated_steps: 6
estimated_files: 2
---

# T01: Implement atomic debt update and payment rerouting flow

**Slice:** S02 — Payment rerouting engine
**Milestone:** M001

## Description

Replace the naive `update_arrangement_repaid` with an atomic SQL UPDATE that caps at remaining debt and transitions status to "completed" when debt hits zero. Then implement the full `on_invoice_paid` handler in tasks.py: tag guard → arrangement lookup → cap calculation → atomic debt update → internal transfer → rollback on failure.

## Steps

1. In `crud.py`, rewrite `update_arrangement_repaid` to use a single SQL UPDATE with CASE expressions for both `repaid_sats` (capped at `total_debt_sats`) and `status` (transitions to "completed" when fully repaid). Add `WHERE status = 'active'` guard. Follow with a SELECT inside the same `db.connect()` context to return the updated arrangement. Return None if no row was updated (arrangement already completed or doesn't exist).
2. In `crud.py`, add a `rollback_arrangement_repaid(arrangement_id, sats)` function that decrements `repaid_sats` by the given amount and resets status to "active" if it was just set to "completed". Use `db.connect()` context for atomicity.
3. In `tasks.py`, implement `on_invoice_paid`: check tag guard (`payment.extra.get("tag") == "orangepiller"`), call `get_arrangement_by_merchant_wallet(payment.wallet_id)`, check arrangement exists and is active, calculate `reroute_sats = min(payment.sat * arrangement.reroute_percent // 100, arrangement.remaining_debt)`, skip if ≤ 0.
4. Continue `on_invoice_paid`: call atomic `update_arrangement_repaid`, then `create_invoice(wallet_id=arrangement.orange_piller_wallet, amount=reroute_sats, internal=True, memo=...)`, then `pay_invoice(wallet_id=arrangement.merchant_wallet, payment_request=..., extra={"tag": "orangepiller"})`.
5. Wrap the transfer (create_invoice + pay_invoice) in try/except. On failure, call `rollback_arrangement_repaid` and log at WARNING level.
6. Add structured loguru logging: INFO for successful reroute (arrangement_id, payment_hash, reroute_sats, new_repaid, remaining); WARNING for rollback; DEBUG for skip reasons (tag guard, no arrangement, zero amount, completed).

## Must-Haves

- [ ] Atomic SQL UPDATE with CASE cap — no read-then-update race
- [ ] `WHERE status = 'active'` prevents rerouting on completed arrangements
- [ ] Tag guard prevents infinite loop on rerouted payments
- [ ] `payment.sat` used (not `payment.amount` msat)
- [ ] `reroute_sats = min(calculated, remaining_debt)` — never overpays
- [ ] Zero-amount skip (reroute_sats ≤ 0 → no transfer)
- [ ] Debt rollback on pay_invoice failure
- [ ] `create_invoice(internal=True)` for same-instance transfer

## Verification

- `python -c "from orangepiller.crud import update_arrangement_repaid; print('ok')"` imports without error
- `python -c "from orangepiller.tasks import on_invoice_paid; print('ok')"` imports without error
- Code inspection: SQL UPDATE uses CASE for both repaid_sats and status
- Code inspection: on_invoice_paid has tag guard, arrangement lookup, cap calc, transfer, rollback

## Inputs

- `orangepiller/crud.py` — existing `update_arrangement_repaid` (naive increment, needs replacement), `get_arrangement_by_merchant_wallet`
- `orangepiller/tasks.py` — skeleton with listener loop and tag guard (log only)
- `orangepiller/models.py` — `Arrangement` model with `remaining_debt` property
- S02-RESEARCH.md — atomic SQL pattern, splitpayments reference, msat/sat conversion rules

## Observability Impact

- **New signals:** loguru INFO on every successful reroute (arrangement_id, payment_hash, reroute_sats, repaid/total, remaining, status). WARNING on pay_invoice failure with rollback details + exception. DEBUG on skip reasons (tag guard, no arrangement, zero amount, completed).
- **Inspection:** Query `orangepiller.arrangements` table — `repaid_sats` and `status` columns reflect current state after each reroute.
- **Failure state:** If `pay_invoice` fails, WARNING log includes exception + rollback confirmation. `repaid_sats` is rolled back to pre-attempt value.
- **Agent verification:** `grep "orangepiller: rerouted" <logfile>` to confirm reroutes; `grep "rolling back"` to find failures.

## Expected Output

- `orangepiller/crud.py` — atomic `update_arrangement_repaid` with cap + status transition + rollback function
- `orangepiller/tasks.py` — complete `on_invoice_paid` with tag guard, cap, transfer, rollback, logging
