from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from lnbits.core.models import WalletTypeInfo
from lnbits.core.services.users import create_user_account_no_ckeck
from lnbits.decorators import require_admin_key

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
    extension auto-enabled), extracts the wallet ID, and stores the
    payback arrangement.
    """
    if data.total_debt_sats <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="total_debt_sats must be greater than 0",
        )
    if not (1 <= data.reroute_percent <= 100):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="reroute_percent must be between 1 and 100",
        )

    try:
        user = await create_user_account_no_ckeck(
            default_exts=["orangepiller"],
        )
    except Exception as exc:
        logger.error(f"Failed to create merchant account: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create merchant account",
        ) from exc

    merchant_wallet = user.wallets[0].id
    merchant_user_id = user.id

    arrangement = await create_arrangement(
        orange_piller_wallet=key_info.wallet.id,
        merchant_wallet=merchant_wallet,
        merchant_user_id=merchant_user_id,
        data=data,
    )

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
        updated = await update_arrangement(
            arrangement_id,
            repaid_sats=arrangement.total_debt_sats,
            status="completed",
        )
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
