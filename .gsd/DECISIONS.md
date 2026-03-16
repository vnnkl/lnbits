# Decisions Register

<!-- Append-only. Never edit or remove existing rows.
     To reverse a decision, add a new row that supersedes it.
     Read this file at the start of any planning or research phase. -->

| # | When | Scope | Decision | Choice | Rationale | Revisable? |
|---|------|-------|----------|--------|-----------|------------|
| 1 | 2026-03-16 | M001/S01 | Extension code identifier | `orangepiller` (lowercase, no dashes) | LNbits convention for extension IDs — used in DB schema prefix, router prefix, static file paths, and `default_exts` parameter | No |
| 2 | 2026-03-16 | M001/S01 | CRUD update pattern | `update_arrangement` accepts `**kwargs` for flexible field updates | Allows T02/S04 to update any combination of fields without creating separate update functions per field | Yes |
| 3 | 2026-03-16 | M001/S01 | Pydantic v1 computed properties | `@property` for `remaining_debt`, `progress_percent`, `is_completed` | Pydantic v1 doesn't support `@computed_field`; properties work but aren't included in `.dict()` serialization — API responses must add them explicitly if needed | Yes |
