# Decisions Register

<!-- Append-only. Never edit or remove existing rows.
     To reverse a decision, add a new row that supersedes it.
     Read this file at the start of any planning or research phase. -->

| # | When | Scope | Decision | Choice | Rationale | Revisable? |
|---|------|-------|----------|--------|-----------|------------|
| D001 | M001 | arch | Debt denomination | Sats | No exchange rate dependencies, simpler tracking, user preference | No |
| D002 | M001 | arch | Payback destination | Same LNbits instance (internal transfer) | Instant, free, can't fail due to routing. User preference | Yes — if external wallets needed |
| D003 | M001 | arch | Extension repo location | Standalone repo (like splitpayments) | LNbits convention for distributable extensions | No |
| D004 | M001 | pattern | Payment interception pattern | register_invoice_listener + asyncio.Queue | Proven pattern used by splitpayments, official LNbits mechanism | No |
| D005 | M001 | convention | Extension code identifier | orangepiller | Lowercase alphanumeric, no dashes — LNbits convention | No |
| D006 | M001 | arch | Account creation method | create_user_account_no_ckeck with default_exts | Core service that handles account + wallet + extension activation atomically | No |
| D007 | M001 | scope | Merchant dispute mechanism | Not implemented | Merchant accepted cash upfront — nothing to dispute. User decision | No |
| D008 | M001 | scope | Store map listing | Deferred | Not needed in first version per user. Could be separate extension | Yes — future milestone |
