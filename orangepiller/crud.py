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
    await db.execute(
        "UPDATE orangepiller.arrangements"
        " SET repaid_sats = repaid_sats + :sats"
        " WHERE id = :id",
        {"sats": additional_sats, "id": arrangement_id},
    )
    return await get_arrangement(arrangement_id)


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
