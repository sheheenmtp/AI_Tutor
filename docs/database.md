# Database

Both applications use PostgreSQL via SQLAlchemy. The primary env var is `DATABASE_URL`.

Course Tutor includes migration helpers in `course_tutor/backend/migration.py` and some legacy SQL in `course_tutor/ops/migrations/legacy/`.

Do not commit database dumps or credentials.
