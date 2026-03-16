import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from lnbits.core.crud.extensions import get_installed_extension
from lnbits.core.models import WalletTypeInfo
from lnbits.core.services.users import create_user_account_no_ckeck
from lnbits.decorators import require_admin_key
from lnbits.settings import settings

from .crud import (
    create_arrangement,
    get_arrangement,
    get_arrangement_by_merchant_wallet,
    get_arrangements_by_piller,
    update_arrangement,
)
from .models import Arrangement, CreateArrangement, UpdateArrangement

orangepiller_ext_api = APIRouter(
    prefix="/api/v1",
    tags=["orangepiller"],
)


@orangepiller_ext_api.post(
    "/arrangements",
    status_code=status.HTTP_201_CREATED,
    response_model=Arrangement,
)
async def api_create_arrangement(
    data: CreateArrangement,
    key_info: WalletTypeInfo = Depends(require_admin_key),
):
    """Create a new payback arrangement.

    Atomically creates a merchant LNbits account (with orangepiller
    extension auto-enabled), extracts the wallet ID, conditionally
    provisions a TPoS terminal, and stores the payback arrangement.
    """
    if data.debt_currency == "sat":
        if data.total_debt_sats <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="total_debt_sats must be greater than 0",
            )
    else:
        if not data.total_debt_fiat or data.total_debt_fiat <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="total_debt_fiat must be greater than 0 for fiat debt",
            )
    if not (1 <= data.reroute_percent <= 100):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="reroute_percent must be between 1 and 100",
        )

    # Step 2: Detect TPoS installation
    tpos_installed = await get_installed_extension("tpos")

    # Step 3: Conditional default_exts
    default_exts = (
        ["orangepiller", "tpos"] if tpos_installed else ["orangepiller"]
    )

    try:
        user = await create_user_account_no_ckeck(
            default_exts=default_exts,
        )
    except Exception as exc:
        logger.error(f"Failed to create merchant account: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create merchant account",
        ) from exc

    merchant_wallet = user.wallets[0].id
    merchant_user_id = user.id

    # Step 4: Construct base URL and merchant credentials
    base_url = settings.lnbits_baseurl.rstrip("/")
    merchant_credentials = f"{base_url}/wallet?usr={user.id}"

    # Steps 5-7: TPoS provisioning (conditional)
    tpos_id = None
    tpos_url = None
    warning = None

    if tpos_installed:
        try:
            tpos_payload = {
                "name": data.merchant_name or "Terminal",
                "currency": data.currency,
                "tip_options": data.tip_options or "[]",
                "tax_default": data.tax_default,
                "tax_inclusive": data.tax_inclusive,
                "business_name": data.business_name,
                "business_address": data.business_address,
                "business_vat_id": data.business_vat_id,
                "wallet": merchant_wallet,
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{base_url}/tpos/api/v1/tposs",
                    json=tpos_payload,
                    headers={"X-Api-Key": user.wallets[0].adminkey},
                )
                resp.raise_for_status()
                resp_json = resp.json()

            tpos_id = resp_json["id"]
            tpos_url = f"{base_url}/tpos/{tpos_id}"
            logger.info(
                f"TPoS provisioned: tpos_id={tpos_id}, "
                f"arrangement merchant_user_id={merchant_user_id}"
            )
        except Exception as exc:
            tpos_id = None
            tpos_url = None
            warning = f"TPoS provisioning failed: {str(exc)}"
            logger.warning(
                f"TPoS provisioning failed for "
                f"merchant_user_id={merchant_user_id}: {exc}"
            )
    else:
        warning = (
            "TPoS extension is not installed. "
            "Arrangement created without a payment terminal."
        )
        logger.warning(
            "TPoS extension not installed — "
            f"arrangement for merchant_user_id={merchant_user_id} "
            "created without TPoS terminal"
        )

    # Step 8: Create arrangement with new fields
    arrangement = await create_arrangement(
        orange_piller_wallet=key_info.wallet.id,
        merchant_wallet=merchant_wallet,
        merchant_user_id=merchant_user_id,
        data=data,
        tpos_id=tpos_id,
        tpos_url=tpos_url,
        merchant_credentials=merchant_credentials,
    )

    # Step 9: Set warning (response-only, not persisted)
    arrangement.warning = warning

    logger.info(
        f"Arrangement created: id={arrangement.id}, "
        f"merchant_user_id={merchant_user_id}, "
        f"merchant_wallet_id={merchant_wallet}"
    )

    return arrangement


@orangepiller_ext_api.get(
    "/arrangements",
    response_model=list[Arrangement],
)
async def api_get_arrangements(
    key_info: WalletTypeInfo = Depends(require_admin_key),
):
    """List all arrangements for the authenticated wallet."""
    return await get_arrangements_by_piller(key_info.wallet.id)


@orangepiller_ext_api.get(
    "/merchant/arrangements",
    response_model=list[Arrangement],
)
async def api_get_merchant_arrangements(
    key_info: WalletTypeInfo = Depends(require_admin_key),
):
    """List arrangements where the authenticated wallet is the merchant."""
    arrangement = await get_arrangement_by_merchant_wallet(key_info.wallet.id)
    if arrangement is None:
        return []
    return [arrangement]


@orangepiller_ext_api.put(
    "/arrangements/{arrangement_id}",
    response_model=Arrangement,
)
async def api_update_arrangement(
    arrangement_id: str,
    data: UpdateArrangement,
    key_info: WalletTypeInfo = Depends(require_admin_key),
):
    """Update an arrangement (reroute percent or forgive debt)."""
    arrangement = await get_arrangement(arrangement_id)
    if arrangement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arrangement not found",
        )

    if arrangement.orange_piller_wallet != key_info.wallet.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this arrangement",
        )

    if data.forgive:
        if arrangement.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot forgive a completed arrangement",
            )
        forgive_kwargs = {
            "repaid_sats": arrangement.total_debt_sats,
            "status": "completed",
        }
        if arrangement.debt_currency != "sat" and arrangement.total_debt_fiat:
            forgive_kwargs["repaid_fiat"] = arrangement.total_debt_fiat
        updated = await update_arrangement(arrangement_id, **forgive_kwargs)
        logger.info(
            f"Arrangement updated: id={arrangement_id}, "
            f"action=forgive, repaid_sats={arrangement.total_debt_sats}"
        )
        return updated

    if data.reroute_percent is not None:
        if not (1 <= data.reroute_percent <= 100):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="reroute_percent must be between 1 and 100",
            )
        if arrangement.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update a completed arrangement",
            )
        updated = await update_arrangement(
            arrangement_id,
            reroute_percent=data.reroute_percent,
        )
        logger.info(
            f"Arrangement updated: id={arrangement_id}, "
            f"action=percent_change, reroute_percent={data.reroute_percent}"
        )
        return updated

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="No update fields provided",
    )
