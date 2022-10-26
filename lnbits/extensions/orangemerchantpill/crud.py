from typing import List, Optional, Union

from lnbits.db import SQLITE

from . import db
from .models import CreatePillLinkData, PillLink


async def create_pill_link(data: CreatePillLinkData, wallet_id: str) -> PillLink:

    returning = "" if db.type == SQLITE else "RETURNING ID"
    method = db.execute if db.type == SQLITE else db.fetchone

    result = await (method)(
        f"""
        INSERT INTO orangepill.pill_links (
            wallet,
            description,
            min,
            max,
            served_meta,
            served_pr,
            webhook_url,
            success_text,
            success_url,
            comment_chars,
            currency,
            fiat_base_multiplier
        )
        VALUES (?, ?, ?, ?, 0, 0, ?, ?, ?, ?, ?, ?)
        {returning}
        """,
        (
            wallet_id,
            data.description,
            data.min,
            data.max,
            data.webhook_url,
            data.success_text,
            data.success_url,
            data.comment_chars,
            data.currency,
            data.fiat_base_multiplier,
        ),
    )
    if db.type == SQLITE:
        link_id = result._result_proxy.lastrowid
    else:
        link_id = result[0]

    link = await get_pill_link(link_id)
    assert link, "Newly created link couldn't be retrieved"
    return link


async def get_pill_link(link_id: int) -> Optional[PillLink]:
    row = await db.fetchone("SELECT * FROM orangepill.pill_links WHERE id = ?", (link_id,))
    return PillLink.from_row(row) if row else None


async def get_pill_links(wallet_ids: Union[str, List[str]]) -> List[PillLink]:
    if isinstance(wallet_ids, str):
        wallet_ids = [wallet_ids]

    q = ",".join(["?"] * len(wallet_ids))
    rows = await db.fetchall(
        f"""
        SELECT * FROM orangepill.pill_links WHERE wallet IN ({q})
        ORDER BY Id
        """,
        (*wallet_ids,),
    )
    return [PillLink.from_row(row) for row in rows]


async def update_pill_link(link_id: int, **kwargs) -> Optional[PillLink]:
    q = ", ".join([f"{field[0]} = ?" for field in kwargs.items()])
    await db.execute(
        f"UPDATE orangepill.pill_links SET {q} WHERE id = ?", (*kwargs.values(), link_id)
    )
    row = await db.fetchone("SELECT * FROM orangepill.pill_links WHERE id = ?", (link_id,))
    return PillLink.from_row(row) if row else None


async def increment_pill_link(link_id: int, **kwargs) -> Optional[PillLink]:
    q = ", ".join([f"{field[0]} = {field[0]} + ?" for field in kwargs.items()])
    await db.execute(
        f"UPDATE orangepill.pill_links SET {q} WHERE id = ?", (*kwargs.values(), link_id)
    )
    row = await db.fetchone("SELECT * FROM orangepill.pill_links WHERE id = ?", (link_id,))
    return PillLink.from_row(row) if row else None


async def delete_pill_link(link_id: int) -> None:
    await db.execute("DELETE FROM orangepill.pill_links WHERE id = ?", (link_id,))
