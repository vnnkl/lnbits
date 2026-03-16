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


async def m002_tpos_fields(db: Connection):
    """
    Add TPoS and merchant fields to arrangements table.
    """
    await db.execute(
        "ALTER TABLE orangepiller.arrangements ADD COLUMN tpos_id TEXT DEFAULT NULL"
    )
    await db.execute(
        "ALTER TABLE orangepiller.arrangements ADD COLUMN tpos_url TEXT DEFAULT NULL"
    )
    await db.execute(
        "ALTER TABLE orangepiller.arrangements ADD COLUMN merchant_name TEXT DEFAULT NULL"
    )
    await db.execute(
        "ALTER TABLE orangepiller.arrangements ADD COLUMN merchant_credentials TEXT DEFAULT NULL"
    )


async def m003_fiat_fields(db: Connection):
    """
    Add fiat-denominated debt tracking fields to arrangements table.
    """
    await db.execute(
        "ALTER TABLE orangepiller.arrangements"
        " ADD COLUMN debt_currency TEXT DEFAULT 'sat'"
    )
    await db.execute(
        "ALTER TABLE orangepiller.arrangements"
        " ADD COLUMN total_debt_fiat REAL DEFAULT NULL"
    )
    await db.execute(
        "ALTER TABLE orangepiller.arrangements"
        " ADD COLUMN repaid_fiat REAL DEFAULT 0"
    )
