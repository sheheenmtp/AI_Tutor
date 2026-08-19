# Legacy database snapshot

`linux_course_pre_lesson_migration.sql` is a sanitized PostgreSQL snapshot from before the lesson-schema migration. It is retained only as a rollback aid for installations using matching pre-migration application code, not as a fresh-install content bootstrap.

The checked-in copy intentionally contains no user accounts, password hashes, session tokens, or learner progress/state rows. Database ownership statements were also removed so the snapshot does not depend on a local PostgreSQL role.

See `backend/rollback_lesson_migration.md` for the restore procedure. The running application continues to use `backend/migration.py` as its migration source of truth.

The current direct migration path still raises `NoSuchTableError: lab_tasks` when started against this restored legacy schema. Resolve and retest that migration behavior before using the snapshot for an in-place upgrade.
