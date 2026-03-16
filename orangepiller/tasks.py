import asyncio

from lnbits.core.models import Payment
from lnbits.core.services import create_invoice, pay_invoice
from lnbits.tasks import register_invoice_listener
from loguru import logger

from .crud import (
    get_arrangement_by_merchant_wallet,
    rollback_arrangement_repaid,
    update_arrangement_repaid,
)


async def wait_for_paid_invoices():
    invoice_queue = asyncio.Queue()
    register_invoice_listener(invoice_queue, "ext_orangepiller")

    while True:
        payment = await invoice_queue.get()
        await on_invoice_paid(payment)


async def on_invoice_paid(payment: Payment) -> None:
    # Tag guard: skip rerouted payments to prevent infinite loop
    if payment.extra.get("tag") == "orangepiller":
        logger.debug(
            f"orangepiller: skipping tagged payment {payment.payment_hash}"
        )
        return

    # Lookup active arrangement for this merchant wallet
    arrangement = await get_arrangement_by_merchant_wallet(payment.wallet_id)
    if not arrangement:
        logger.debug(
            f"orangepiller: no arrangement for wallet {payment.wallet_id}"
        )
        return

    if arrangement.status != "active":
        logger.debug(
            f"orangepiller: arrangement {arrangement.id} is {arrangement.status}, "
            "skipping"
        )
        return

    # Calculate reroute amount (sats), capped at remaining debt
    reroute_sats = min(
        payment.sat * arrangement.reroute_percent // 100,
        arrangement.remaining_debt,
    )
    if reroute_sats <= 0:
        logger.debug(
            f"orangepiller: zero reroute for arrangement {arrangement.id} "
            f"(payment={payment.sat} sats, remaining={arrangement.remaining_debt})"
        )
        return

    # Atomic debt update — caps at total_debt_sats, transitions status
    updated = await update_arrangement_repaid(arrangement.id, reroute_sats)
    if not updated:
        logger.debug(
            f"orangepiller: arrangement {arrangement.id} no longer active "
            "after atomic update"
        )
        return

    # Internal transfer: create invoice on orange piller wallet, pay from merchant
    try:
        memo = (
            f"orangepiller reroute: {reroute_sats} sats"
            f" from {arrangement.merchant_wallet}"
            f" ({arrangement.reroute_percent}%)"
            f";{payment.payment_hash}"
        )
        new_payment = await create_invoice(
            wallet_id=arrangement.orange_piller_wallet,
            amount=reroute_sats,
            internal=True,
            memo=memo,
        )
        await pay_invoice(
            wallet_id=arrangement.merchant_wallet,
            payment_request=new_payment.bolt11,
            extra={"tag": "orangepiller"},
        )
    except Exception as exc:
        logger.warning(
            f"orangepiller: transfer failed for arrangement {arrangement.id}, "
            f"rolling back {reroute_sats} sats — {exc}"
        )
        await rollback_arrangement_repaid(arrangement.id, reroute_sats)
        return

    logger.info(
        f"orangepiller: rerouted {reroute_sats} sats"
        f" | arrangement={arrangement.id}"
        f" | payment_hash={payment.payment_hash}"
        f" | repaid={updated.repaid_sats}/{updated.total_debt_sats}"
        f" | remaining={updated.remaining_debt}"
        f" | status={updated.status}"
    )
