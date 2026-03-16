from lnbits.db import Connection


async def m001_initial(db: Connection):
    """
    Initial orangepiller arrangements table.
    """
    await db.execute(
        f"""
        CREATE TABLE orangepiller.arrangements (
            id TEXT PRIMARY KEY,
            orange_piller_wallet TEXT NOT NULL,
            merchant_wallet TEXT NOT NULL,
            merchant_user_id TEXT NOT NULL,
            total_debt_sats INTEGER NOT NULL,
            repaid_sats INTEGER NOT NULL DEFAULT 0,
            reroute_percent INTEGER NOT NULL CHECK (reroute_percent >= 0 AND reroute_percent <= 100),
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP NOT NULL DEFAULT {db.timestamp_now}
        );
    """
    )
