from typing import Optional

from lnbits.db import Database
from lnbits.helpers import urlsafe_short_hash

from .models import Arrangement, CreateArrangement

db = Database("ext_orangepiller")


async def create_arrangement(
    orange_piller_wallet: str,
    merchant_wallet: str,
    merchant_user_id: str,
    data: CreateArrangement,
    tpos_id: Optional[str] = None,
    tpos_url: Optional[str] = None,
    merchant_credentials: Optional[str] = None,
) -> Arrangement:
    arrangement_id = urlsafe_short_hash()
    arrangement = Arrangement(
        id=arrangement_id,
        orange_piller_wallet=orange_piller_wallet,
        merchant_wallet=merchant_wallet,
        merchant_user_id=merchant_user_id,
        total_debt_sats=data.total_debt_sats,
        repaid_sats=0,
        reroute_percent=data.reroute_percent,
        status="active",
        tpos_id=tpos_id,
        tpos_url=tpos_url,
        merchant_name=data.merchant_name,
        merchant_credentials=merchant_credentials,
        debt_currency=data.debt_currency,
        total_debt_fiat=data.total_debt_fiat,
        repaid_fiat=0,
    )
    await db.insert("orangepiller.arrangements", arrangement)
    return arrangement


async def get_arrangement(arrangement_id: str) -> Optional[Arrangement]:
    return await db.fetchone(
        "SELECT * FROM orangepiller.arrangements WHERE id = :id",
        {"id": arrangement_id},
        Arrangement,
    )


async def get_arrangements_by_piller(
    orange_piller_wallet: str,
) -> list[Arrangement]:
    return await db.fetchall(
        "SELECT * FROM orangepiller.arrangements"
        " WHERE orange_piller_wallet = :wallet",
        {"wallet": orange_piller_wallet},
        Arrangement,
    )


async def get_arrangement_by_merchant_wallet(
    merchant_wallet: str,
) -> Optional[Arrangement]:
    return await db.fetchone(
        "SELECT * FROM orangepiller.arrangements"
        " WHERE merchant_wallet = :wallet",
        {"wallet": merchant_wallet},
        Arrangement,
    )


async def update_arrangement_repaid(
    arrangement_id: str,
    additional_sats: int,
) -> Optional[Arrangement]:
    """Atomically increment repaid_sats (capped at total_debt_sats) and
    transition status to 'completed' when fully repaid.

    Returns the updated Arrangement, or None if no active arrangement
    was found (already completed or doesn't exist).
    """
    async with db.connect() as conn:
        result = await conn.execute(
            """
            UPDATE orangepiller.arrangements
            SET repaid_sats = CASE
                    WHEN repaid_sats + :sats > total_debt_sats
                        THEN total_debt_sats
                    ELSE repaid_sats + :sats
                END,
                status = CASE
                    WHEN repaid_sats + :sats >= total_debt_sats
                        THEN 'completed'
                    ELSE status
                END
            WHERE id = :id AND status = 'active'
            """,
            {"sats": additional_sats, "id": arrangement_id},
        )
        if result.rowcount == 0:  # type: ignore
            return None
        return await conn.fetchone(
            "SELECT * FROM orangepiller.arrangements WHERE id = :id",
            {"id": arrangement_id},
            Arrangement,
        )


async def update_arrangement_repaid_fiat(
    arrangement_id: str,
    additional_fiat: float,
) -> Optional[Arrangement]:
    """Atomically increment repaid_fiat (capped at total_debt_fiat) and
    transition status to 'completed' when fully repaid.

    Returns the updated Arrangement, or None if no active arrangement
    was found (already completed or doesn't exist).
    """
    async with db.connect() as conn:
        result = await conn.execute(
            """
            UPDATE orangepiller.arrangements
            SET repaid_fiat = CASE
                    WHEN repaid_fiat + :fiat > total_debt_fiat
                        THEN total_debt_fiat
                    ELSE repaid_fiat + :fiat
                END,
                status = CASE
                    WHEN repaid_fiat + :fiat >= total_debt_fiat
                        THEN 'completed'
                    ELSE status
                END
            WHERE id = :id AND status = 'active'
            """,
            {"fiat": additional_fiat, "id": arrangement_id},
        )
        if result.rowcount == 0:  # type: ignore
            return None
        return await conn.fetchone(
            "SELECT * FROM orangepiller.arrangements WHERE id = :id",
            {"id": arrangement_id},
            Arrangement,
        )


async def rollback_arrangement_repaid(
    arrangement_id: str,
    sats: int,
) -> None:
    """Roll back a debt update after a failed payment transfer.

    Decrements repaid_sats by the given amount and resets status
    to 'active' if it was set to 'completed'.
    """
    async with db.connect() as conn:
        await conn.execute(
            """
            UPDATE orangepiller.arrangements
            SET repaid_sats = CASE
                    WHEN repaid_sats - :sats < 0 THEN 0
                    ELSE repaid_sats - :sats
                END,
                status = 'active'
            WHERE id = :id
            """,
            {"sats": sats, "id": arrangement_id},
        )


async def rollback_arrangement_repaid_fiat(
    arrangement_id: str,
    fiat_amount: float,
) -> None:
    """Roll back a fiat debt update after a failed payment transfer.

    Decrements repaid_fiat by the given amount and resets status
    to 'active' if it was set to 'completed'.
    """
    async with db.connect() as conn:
        await conn.execute(
            """
            UPDATE orangepiller.arrangements
            SET repaid_fiat = CASE
                    WHEN repaid_fiat - :fiat < 0 THEN 0
                    ELSE repaid_fiat - :fiat
                END,
                status = 'active'
            WHERE id = :id
            """,
            {"fiat": fiat_amount, "id": arrangement_id},
        )


async def update_arrangement(
    arrangement_id: str,
    **kwargs,
) -> Optional[Arrangement]:
    set_clause = ", ".join(f"{k} = :{k}" for k in kwargs)
    params = {**kwargs, "id": arrangement_id}
    await db.execute(
        f"UPDATE orangepiller.arrangements SET {set_clause} WHERE id = :id",
        params,
    )
    return await get_arrangement(arrangement_id)
