# Shared components

This directory is reserved for genuinely shared code used by multiple applications.

Criteria for placing code here:
- Pure utilities with no application-specific business logic (string helpers, small adapters).
- Configuration helpers that standardize loading environment variables (keep secrets out of repo).
- Shared pydantic schemas or DTOs used by both backends (only if identical semantic meaning).

Do NOT move application-specific models, database schema, or route handlers here. When in doubt, keep code in its originating app and only extract once tests demonstrate identical behavior.

Planned subfolders:
- `shared/config/` — env helpers and configuration schemas
- `shared/utils/` — small, well-tested helpers
- `shared/schemas/` — cross-app pydantic schemas (if needed)
