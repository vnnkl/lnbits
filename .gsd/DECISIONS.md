# Decisions Register

<!-- Append-only. Never edit or remove existing rows.
     To reverse a decision, add a new row that supersedes it.
     Read this file at the start of any planning or research phase. -->

| # | When | Scope | Decision | Choice | Rationale | Revisable? |
|---|------|-------|----------|--------|-----------|------------|
| 1 | 2026-03-16 | M001/S01 | Extension code identifier | `orangepiller` (lowercase, no dashes) | LNbits convention for extension IDs — used in DB schema prefix, router prefix, static file paths, and `default_exts` parameter | No |
| 2 | 2026-03-16 | M001/S01 | CRUD update pattern | `update_arrangement` accepts `**kwargs` for flexible field updates | Allows T02/S04 to update any combination of fields without creating separate update functions per field | Yes |
| 3 | 2026-03-16 | M001/S01 | Pydantic v1 computed properties | `@property` for `remaining_debt`, `progress_percent`, `is_completed` | Pydantic v1 doesn't support `@computed_field`; properties work but aren't included in `.dict()` serialization — API responses must add them explicitly if needed | Yes |
| 4 | 2026-03-16 | M001/S02 | Atomic debt update strategy | SQL UPDATE with CASE cap + SELECT within `db.connect()` context | Avoids read-then-update race for concurrent payments; avoids `RETURNING` clause for SQLite < 3.35 portability | No |
| 5 | 2026-03-16 | M001/S02 | Debt update before transfer | Update debt first, rollback if `pay_invoice` fails | Prevents concurrent payments from both reading the same remaining_debt; rollback handles transfer failure safely | Yes |
| 6 | 2026-03-16 | M001/S03 | Computed fields in JS not API | `remaining_debt` and `progress_percent` computed client-side from `total_debt_sats` and `repaid_sats` | Pydantic v1 `@property` fields aren't included in `.dict()` serialization; computing in JS avoids touching model serialization | No |
| 7 | 2026-03-16 | M001/S04 | Single UpdateArrangement model for PUT | `UpdateArrangement` with `reroute_percent: Optional[int]` and `forgive: Optional[bool]` — one endpoint handles both operations | Cleaner than separate endpoints; `update_arrangement(**kwargs)` CRUD already supports flexible updates | No |
| 8 | 2026-03-16 | M001/S05 | Extension packaging follows splitpayments pattern | config.json fields, file layout, min_lnbits_version=1.3.0 | Proven convention from existing LNbits extensions; 1.3.0 covers all APIs used | No |
| 9 | 2026-03-16 | M001/S05 | Transition-aware toast notifications | Compare old vs new arrangement arrays by id; fire toast only on actual status transition | Prevents false notifications on initial page load or refresh without changes | Yes |
