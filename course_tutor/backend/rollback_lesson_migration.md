# Rollback Strategy

This migration was applied with two rollback layers:

1. Full PostgreSQL dump created before restructuring:
   - `ops/migrations/legacy/linux_course_pre_lesson_migration.sql`
2. In-database backup tables created by the migration:
   - `backup_courses`
   - `backup_modules`
   - `backup_topics`
   - `backup_sublevels`
   - `backup_explanations`
   - `backup_questions`
   - `backup_user_progress`
   - `backup_user_state`
   - `backup_users`

## Recommended rollback order

### Option 1: Full database restore

Use this if the migrated database should be fully reverted to the exact pre-migration state.

```bash
: "${DATABASE_ADMIN_URL:?Set DATABASE_ADMIN_URL to the PostgreSQL administrative database URL}"
: "${DATABASE_URL:?Set DATABASE_URL to the application database URL}"

psql "$DATABASE_ADMIN_URL" -c "DROP DATABASE IF EXISTS linux_course;"
psql "$DATABASE_ADMIN_URL" -c "CREATE DATABASE linux_course;"
psql "$DATABASE_URL" -f ops/migrations/legacy/linux_course_pre_lesson_migration.sql
```

### Option 2: Table-level rollback inside the same database

Use this if you want to revert schema/data without recreating the whole database.

High-level rollback steps:

1. Stop the backend.
2. Drop or rename migrated tables:
   - `lessons`
   - `lesson_contents`
   - `user_lesson_progress`
3. Restore altered tables from backups:
   - `courses`
   - `modules`
   - `topics`
   - `questions`
   - `user_state`
   - `users`
4. Restore legacy working tables from backups:
   - `sublevels`
   - `explanations`
   - `user_progress`
5. Switch backend code back to the pre-migration model layer.

Example SQL outline:

```sql
BEGIN;

DROP TABLE IF EXISTS user_lesson_progress;
DROP TABLE IF EXISTS lesson_contents;
DROP TABLE IF EXISTS lessons;

TRUNCATE TABLE questions CASCADE;
INSERT INTO questions SELECT * FROM backup_questions;

TRUNCATE TABLE topics CASCADE;
INSERT INTO topics SELECT * FROM backup_topics;

TRUNCATE TABLE modules CASCADE;
INSERT INTO modules SELECT * FROM backup_modules;

TRUNCATE TABLE courses CASCADE;
INSERT INTO courses SELECT * FROM backup_courses;

TRUNCATE TABLE user_state CASCADE;
INSERT INTO user_state SELECT * FROM backup_user_state;

TRUNCATE TABLE users CASCADE;
INSERT INTO users SELECT * FROM backup_users;

COMMIT;
```

## Important notes

- Prefer the full SQL dump restore for the safest rollback.
- The checked-in legacy dump is sanitized: user accounts, session tokens, and learner progress rows are intentionally omitted.
- The backend code now targets the lesson-based schema, so code rollback must accompany DB rollback.
- Do not remove backup tables until the new schema has been validated in staging/production workflows.
