import asyncio

from lnbits.core.models import Payment
from lnbits.core.services import create_invoice, pay_invoice
from lnbits.tasks import register_invoice_listener
from lnbits.utils.exchange_rates import (
    fiat_amount_as_satoshis,
    satoshis_amount_as_fiat,
)
from loguru import logger

from .crud import (
    get_arrangement_by_merchant_wallet,
    rollback_arrangement_repaid,
    rollback_arrangement_repaid_fiat,
    update_arrangement_repaid,
    update_arrangement_repaid_fiat,
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

    # Branch: fiat-denominated debt uses spot-rate conversion
    if arrangement.debt_currency != "sat":
        await _handle_fiat_reroute(payment, arrangement)
        return

    # Sat-denominated path (unchanged from M001)
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


async def _handle_fiat_reroute(payment: Payment, arrangement) -> None:
    """Handle rerouting for fiat-denominated debt.

    Converts the incoming sat payment to fiat at spot rate, applies
    reroute %, caps at remaining fiat debt, converts back to sats
    for the actual transfer, and updates fiat debt atomically.
    """
    currency = arrangement.debt_currency

    # Fetch spot rate — skip reroute if exchange rate unavailable
    try:
        fiat_payment_value = await satoshis_amount_as_fiat(
            payment.sat, currency
        )
    except (ValueError, Exception) as exc:
        logger.warning(
            f"orangepiller: exchange rate unavailable for {currency}, "
            f"skipping reroute for arrangement {arrangement.id} — {exc}"
        )
        return

    # Apply reroute % in fiat space, cap at remaining fiat debt
    fiat_reroute = fiat_payment_value * arrangement.reroute_percent / 100
    fiat_reroute = min(fiat_reroute, arrangement.remaining_debt_fiat)

    if fiat_reroute <= 0:
        logger.debug(
            f"orangepiller: zero fiat reroute for arrangement {arrangement.id} "
            f"(payment={payment.sat} sats = {fiat_payment_value:.4f} {currency}, "
            f"remaining={arrangement.remaining_debt_fiat:.2f} {currency})"
        )
        return

    # Convert fiat reroute amount back to sats for the actual transfer
    try:
        reroute_sats = await fiat_amount_as_satoshis(fiat_reroute, currency)
    except (ValueError, Exception) as exc:
        logger.warning(
            f"orangepiller: fiat-to-sat conversion failed for {currency}, "
            f"skipping reroute for arrangement {arrangement.id} — {exc}"
        )
        return

    if reroute_sats <= 0:
        logger.debug(
            f"orangepiller: fiat reroute {fiat_reroute:.4f} {currency} "
            f"converts to 0 sats, skipping arrangement {arrangement.id}"
        )
        return

    # Atomic fiat debt update
    updated = await update_arrangement_repaid_fiat(arrangement.id, fiat_reroute)
    if not updated:
        logger.debug(
            f"orangepiller: arrangement {arrangement.id} no longer active "
            "after fiat atomic update"
        )
        return

    # Internal transfer: sat amount
    try:
        memo = (
            f"orangepiller fiat reroute: {fiat_reroute:.2f} {currency}"
            f" ({reroute_sats} sats)"
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
            f"orangepiller: fiat transfer failed for arrangement "
            f"{arrangement.id}, rolling back {fiat_reroute:.4f} "
            f"{currency} — {exc}"
        )
        await rollback_arrangement_repaid_fiat(arrangement.id, fiat_reroute)
        return

    logger.info(
        f"orangepiller: fiat rerouted {fiat_reroute:.2f} {currency}"
        f" ({reroute_sats} sats)"
        f" | arrangement={arrangement.id}"
        f" | payment_hash={payment.payment_hash}"
        f" | repaid_fiat={updated.repaid_fiat:.2f}/{updated.total_debt_fiat:.2f}"
        f" | remaining_fiat={updated.remaining_debt_fiat:.2f}"
        f" | status={updated.status}"
    )
