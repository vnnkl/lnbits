from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from lnbits.core.models import WalletTypeInfo
from lnbits.core.services.users import create_user_account_no_ckeck
from lnbits.decorators import require_admin_key

from .crud import create_arrangement, get_arrangements_by_piller
from .models import Arrangement, CreateArrangement

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


@orangepiller_ext_api.put(
    "/arrangements/{arrangement_id}",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
)
async def api_update_arrangement(arrangement_id: str):
    """Stub — update logic implemented in S04."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Update not yet implemented (reserved for S04)",
    )
