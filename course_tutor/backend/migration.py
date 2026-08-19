import json
import re
from collections import defaultdict
from typing import Any

from sqlalchemy import inspect, text

from backend.db import engine


def slugify(value: str, fallback: str) -> str:
    lowered = (value or "").strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or fallback


def coerce_jsonb(raw_value: Any) -> Any:
    if raw_value is None:
        return None
    if isinstance(raw_value, (dict, list)):
        return raw_value
    if isinstance(raw_value, str):
        try:
            return json.loads(raw_value)
        except json.JSONDecodeError:
            return {"legacy_raw_text": raw_value}
    return {"legacy_raw_text": str(raw_value)}


def ensure_backup_table(table_name: str) -> None:
    backup_name = f"backup_{table_name}"
    with engine.begin() as connection:
        exists = connection.execute(text("SELECT to_regclass(:name)"), {"name": backup_name}).scalar_one()
        source_exists = connection.execute(text("SELECT to_regclass(:name)"), {"name": table_name}).scalar_one()
        if source_exists and not exists:
            connection.execute(text(f"CREATE TABLE {backup_name} AS TABLE {table_name} WITH DATA"))


def build_scoped_slugs(rows: list[dict[str, Any]], title_key: str, scope_key: str | None = None, existing_slug_key: str | None = None) -> dict[int, str]:
    used: dict[Any, set[str]] = defaultdict(set)
    scoped_slugs: dict[int, str] = {}

    for row in rows:
        scope = row.get(scope_key) if scope_key else "__global__"
        existing_slug = row.get(existing_slug_key) if existing_slug_key else None
        base = slugify(existing_slug or row[title_key], f"item-{row['id']}")
        candidate = base
        suffix = 2
        while candidate in used[scope]:
            candidate = f"{base}-{suffix}"
            suffix += 1
        used[scope].add(candidate)
        scoped_slugs[row["id"]] = candidate

    return scoped_slugs


def create_new_tables_if_needed() -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS lessons (
                    id SERIAL PRIMARY KEY,
                    topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
                    title VARCHAR(255) NOT NULL,
                    slug VARCHAR(255) NOT NULL,
                    sequence INTEGER NOT NULL DEFAULT 1,
                    lesson_type VARCHAR(50) NOT NULL DEFAULT 'concept',
                    difficulty VARCHAR(50) NOT NULL DEFAULT 'beginner',
                    objective TEXT,
                    practice_task TEXT,
                    common_confusions JSONB NOT NULL DEFAULT '[]',
                    examples JSONB NOT NULL DEFAULT '[]',
                    tags JSONB NOT NULL DEFAULT '[]',
                    raw_json JSONB,
                    CONSTRAINT uq_lessons_topic_slug UNIQUE (topic_id, slug)
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS lesson_contents (
                    id SERIAL PRIMARY KEY,
                    lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
                    level VARCHAR(50) NOT NULL,
                    content_type VARCHAR(50) NOT NULL DEFAULT 'explanation',
                    title VARCHAR(255),
                    content TEXT NOT NULL,
                    sequence INTEGER NOT NULL DEFAULT 1
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS practice_exercises (
                    id SERIAL PRIMARY KEY,
                    lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
                    title VARCHAR(255) NOT NULL,
                    prompt TEXT NOT NULL,
                    starter_code TEXT NOT NULL,
                    expected_output TEXT,
                    allowed_commands JSONB NOT NULL DEFAULT '[]',
                    sequence INTEGER NOT NULL DEFAULT 1,
                    is_required BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS labs (
                    id SERIAL PRIMARY KEY,
                    lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
                    title VARCHAR(255) NOT NULL,
                    description TEXT NOT NULL,
                    sequence INTEGER NOT NULL DEFAULT 1,
                    is_required BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS lab_tasks (
                    id SERIAL PRIMARY KEY,
                    lab_id INTEGER NOT NULL REFERENCES labs(id) ON DELETE CASCADE,
                    title VARCHAR(255) NOT NULL,
                    instruction TEXT NOT NULL,
                    starter_code TEXT NOT NULL,
                    expected_output TEXT,
                    allowed_commands JSONB NOT NULL DEFAULT '[]',
                    validation JSONB,
                    sequence INTEGER NOT NULL DEFAULT 1
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS lab_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    lab_id INTEGER NOT NULL REFERENCES labs(id) ON DELETE CASCADE,
                    current_working_directory TEXT NOT NULL DEFAULT '/workspace',
                    command_history JSONB NOT NULL DEFAULT '[]',
                    completed_tasks JSONB NOT NULL DEFAULT '[]',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT uq_lab_sessions_user_lab UNIQUE (user_id, lab_id)
                )
                """
            )
        )
        lab_task_columns = {col["name"] for col in inspect(engine).get_columns("lab_tasks")}
        if "validation" not in lab_task_columns:
            connection.execute(text("ALTER TABLE lab_tasks ADD COLUMN validation JSONB"))
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS user_lesson_progress (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
                    status VARCHAR(50) NOT NULL DEFAULT 'locked',
                    current_level VARCHAR(50) NOT NULL DEFAULT 'standard',
                    read_completed BOOLEAN NOT NULL DEFAULT FALSE,
                    quiz_unlocked BOOLEAN NOT NULL DEFAULT FALSE,
                    quiz_completed BOOLEAN NOT NULL DEFAULT FALSE,
                    last_score INTEGER,
                    best_score INTEGER,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    mastery_status VARCHAR(50) NOT NULL DEFAULT 'not_started',
                    hint_usage INTEGER NOT NULL DEFAULT 0,
                    confidence INTEGER NOT NULL DEFAULT 0,
                    question_history JSONB NOT NULL DEFAULT '[]',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT uq_user_lesson_progress_user_lesson UNIQUE (user_id, lesson_id)
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    session_token TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )


def migrate_courses_modules_topics_users() -> None:
    inspector = inspect(engine)

    with engine.begin() as connection:
        course_columns = {col["name"] for col in inspector.get_columns("courses")}
        if "name" in course_columns and "title" not in course_columns:
            connection.execute(text("ALTER TABLE courses RENAME COLUMN name TO title"))
            course_columns.discard("name")
            course_columns.add("title")
        for ddl in (
            ("slug", "VARCHAR(255)"),
            ("description", "TEXT"),
            ("sequence", "INTEGER NOT NULL DEFAULT 1"),
            ("is_published", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ):
            if ddl[0] not in course_columns:
                connection.execute(text(f"ALTER TABLE courses ADD COLUMN {ddl[0]} {ddl[1]}"))

    with engine.begin() as connection:
        module_columns = {col["name"] for col in inspect(engine).get_columns("modules")}
        if "name" in module_columns and "title" not in module_columns:
            connection.execute(text("ALTER TABLE modules RENAME COLUMN name TO title"))
            module_columns.discard("name")
            module_columns.add("title")
        for ddl in (
            ("slug", "VARCHAR(255)"),
            ("description", "TEXT"),
            ("sequence", "INTEGER NOT NULL DEFAULT 1"),
        ):
            if ddl[0] not in module_columns:
                connection.execute(text(f"ALTER TABLE modules ADD COLUMN {ddl[0]} {ddl[1]}"))

    with engine.begin() as connection:
        topic_columns = {col["name"] for col in inspect(engine).get_columns("topics")}
        if "name" in topic_columns and "title" not in topic_columns:
            connection.execute(text("ALTER TABLE topics RENAME COLUMN name TO title"))
            topic_columns.discard("name")
            topic_columns.add("title")
        for ddl in (
            ("slug", "VARCHAR(255)"),
            ("description", "TEXT"),
        ):
            if ddl[0] not in topic_columns:
                connection.execute(text(f"ALTER TABLE topics ADD COLUMN {ddl[0]} {ddl[1]}"))

    with engine.begin() as connection:
        user_columns = {col["name"] for col in inspect(engine).get_columns("users")}
        if "created_at" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))

    with engine.begin() as connection:
        courses = [dict(row) for row in connection.execute(text("SELECT id, title, slug FROM courses ORDER BY id")).mappings()]
        course_slugs = build_scoped_slugs(courses, "title", existing_slug_key="slug")
        for row in courses:
            connection.execute(
                text(
                    """
                    UPDATE courses
                    SET slug = :slug,
                        sequence = COALESCE(sequence, :sequence),
                        is_published = COALESCE(is_published, FALSE),
                        created_at = COALESCE(created_at, CURRENT_TIMESTAMP)
                    WHERE id = :id
                    """
                ),
                {"id": row["id"], "slug": course_slugs[row["id"]], "sequence": row["id"]},
            )
        connection.execute(text("ALTER TABLE courses ALTER COLUMN title SET NOT NULL"))
        connection.execute(text("ALTER TABLE courses ALTER COLUMN slug SET NOT NULL"))
        connection.execute(text("ALTER TABLE courses ALTER COLUMN sequence SET NOT NULL"))
        connection.execute(text("ALTER TABLE courses ALTER COLUMN sequence SET DEFAULT 1"))
        connection.execute(text("ALTER TABLE courses ALTER COLUMN is_published SET NOT NULL"))
        connection.execute(text("ALTER TABLE courses ALTER COLUMN is_published SET DEFAULT FALSE"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_courses_slug ON courses(slug)"))

        modules = [dict(row) for row in connection.execute(text("SELECT id, course_id, title, slug, sequence FROM modules ORDER BY course_id, id")).mappings()]
        module_slugs = build_scoped_slugs(modules, "title", scope_key="course_id", existing_slug_key="slug")
        for idx, row in enumerate(modules, start=1):
            connection.execute(
                text(
                    """
                    UPDATE modules
                    SET slug = :slug,
                        sequence = COALESCE(sequence, :sequence)
                    WHERE id = :id
                    """
                ),
                {"id": row["id"], "slug": module_slugs[row["id"]], "sequence": idx},
            )
        connection.execute(text("ALTER TABLE modules ALTER COLUMN title SET NOT NULL"))
        connection.execute(text("ALTER TABLE modules ALTER COLUMN slug SET NOT NULL"))
        connection.execute(text("ALTER TABLE modules ALTER COLUMN sequence SET NOT NULL"))
        connection.execute(text("ALTER TABLE modules ALTER COLUMN sequence SET DEFAULT 1"))
        connection.execute(text("DROP INDEX IF EXISTS uq_modules_course_slug"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_modules_course_slug ON modules(course_id, slug)"))

        topic_columns = {col["name"] for col in inspect(engine).get_columns("topics")}
        position_expr = "COALESCE(sequence, position, 1)" if "position" in topic_columns else "COALESCE(sequence, 1)"
        topics = [
            dict(row)
            for row in connection.execute(
                text(
                    f"""
                    SELECT id, module_id, title, slug, description,
                           {position_expr} AS effective_sequence
                    FROM topics
                    ORDER BY module_id, {position_expr}, id
                    """
                )
            ).mappings()
        ]
        topic_slugs = build_scoped_slugs(topics, "title", scope_key="module_id", existing_slug_key="slug")
        per_module_sequence: dict[int, int] = defaultdict(int)
        for row in topics:
            per_module_sequence[row["module_id"]] += 1
            connection.execute(
                text(
                    """
                    UPDATE topics
                    SET slug = :slug,
                        sequence = :sequence
                    WHERE id = :id
                    """
                ),
                {"id": row["id"], "slug": topic_slugs[row["id"]], "sequence": per_module_sequence[row["module_id"]]},
            )
        connection.execute(text("ALTER TABLE topics ALTER COLUMN title SET NOT NULL"))
        connection.execute(text("ALTER TABLE topics ALTER COLUMN slug SET NOT NULL"))
        connection.execute(text("ALTER TABLE topics ALTER COLUMN sequence SET NOT NULL"))
        connection.execute(text("ALTER TABLE topics ALTER COLUMN sequence SET DEFAULT 1"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_topics_module_slug ON topics(module_id, slug)"))


def migrate_lessons() -> None:
    create_new_tables_if_needed()
    if "sublevels" not in inspect(engine).get_table_names():
        return
    with engine.begin() as connection:
        source_rows = [
            dict(row)
            for row in connection.execute(
                text("SELECT id, topic_id, name, slug, sequence, raw_json FROM sublevels ORDER BY id")
            ).mappings()
        ]
        lesson_slugs = build_scoped_slugs(source_rows, "name", scope_key="topic_id", existing_slug_key="slug")
        for row in source_rows:
            raw_json = coerce_jsonb(row["raw_json"])
            payload = raw_json if isinstance(raw_json, dict) else {}
            connection.execute(
                text(
                    """
                    INSERT INTO lessons (
                        id, topic_id, title, slug, sequence, lesson_type, difficulty,
                        objective, practice_task, common_confusions, examples, tags, raw_json
                    ) VALUES (
                        :id, :topic_id, :title, :slug, :sequence, :lesson_type, :difficulty,
                        :objective, :practice_task, CAST(:common_confusions AS JSONB),
                        CAST(:examples AS JSONB), CAST(:tags AS JSONB), CAST(:raw_json AS JSONB)
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        topic_id = EXCLUDED.topic_id,
                        title = EXCLUDED.title,
                        slug = EXCLUDED.slug,
                        sequence = EXCLUDED.sequence,
                        lesson_type = EXCLUDED.lesson_type,
                        difficulty = EXCLUDED.difficulty,
                        objective = EXCLUDED.objective,
                        practice_task = EXCLUDED.practice_task,
                        common_confusions = EXCLUDED.common_confusions,
                        examples = EXCLUDED.examples,
                        tags = EXCLUDED.tags,
                        raw_json = EXCLUDED.raw_json
                    """
                ),
                {
                    "id": row["id"],
                    "topic_id": row["topic_id"],
                    "title": row["name"],
                    "slug": lesson_slugs[row["id"]],
                    "sequence": row["sequence"] or 1,
                    "lesson_type": payload.get("lesson_type", "concept"),
                    "difficulty": payload.get("difficulty", "beginner"),
                    "objective": payload.get("objective"),
                    "practice_task": payload.get("practice_task"),
                    "common_confusions": json.dumps(payload.get("common_confusions", [])),
                    "examples": json.dumps(payload.get("examples", [])),
                    "tags": json.dumps(payload.get("tags", [])),
                    "raw_json": json.dumps(raw_json) if raw_json is not None else None,
                },
            )


def migrate_lesson_contents() -> None:
    create_new_tables_if_needed()
    if "explanations" not in inspect(engine).get_table_names():
        return
    with engine.begin() as connection:
        source_rows = [
            dict(row)
            for row in connection.execute(
                text(
                    """
                    SELECT id, sublevel_id, level, content
                    FROM explanations
                    ORDER BY sublevel_id, level, id
                    """
                )
            ).mappings()
        ]
        per_scope_sequence: dict[tuple[int, str], int] = defaultdict(int)
        for row in source_rows:
            scope = (row["sublevel_id"], row["level"])
            per_scope_sequence[scope] += 1
            connection.execute(
                text(
                    """
                    INSERT INTO lesson_contents (
                        id, lesson_id, level, content_type, title, content, sequence
                    ) VALUES (
                        :id, :lesson_id, :level, 'explanation', NULL, :content, :sequence
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        lesson_id = EXCLUDED.lesson_id,
                        level = EXCLUDED.level,
                        content = EXCLUDED.content,
                        sequence = EXCLUDED.sequence
                    """
                ),
                {
                    "id": row["id"],
                    "lesson_id": row["sublevel_id"],
                    "level": row["level"],
                    "content": row["content"],
                    "sequence": per_scope_sequence[scope],
                },
            )


def migrate_questions() -> None:
    with engine.begin() as connection:
        columns = {col["name"] for col in inspect(engine).get_columns("questions")}
        if "sublevel_id" in columns and "lesson_id" not in columns:
            connection.execute(text("ALTER TABLE questions RENAME COLUMN sublevel_id TO lesson_id"))
            columns.discard("sublevel_id")
            columns.add("lesson_id")
        if "answer" in columns and "correct_answer" not in columns:
            connection.execute(text("ALTER TABLE questions RENAME COLUMN answer TO correct_answer"))
            columns.discard("answer")
            columns.add("correct_answer")
        for ddl in (
            ("question_type", "VARCHAR(50) NOT NULL DEFAULT 'mcq'"),
            ("explanation", "TEXT"),
            ("difficulty", "VARCHAR(50) DEFAULT 'medium'"),
            ("sequence", "INTEGER NOT NULL DEFAULT 1"),
        ):
            if ddl[0] not in columns:
                connection.execute(text(f"ALTER TABLE questions ADD COLUMN {ddl[0]} {ddl[1]}"))
        question_rows = [
            dict(row)
            for row in connection.execute(
                text("SELECT id, lesson_id, level FROM questions ORDER BY lesson_id, level, id")
            ).mappings()
        ]
        per_scope_sequence: dict[tuple[int, str], int] = defaultdict(int)
        for row in question_rows:
            scope = (row["lesson_id"], row["level"])
            per_scope_sequence[scope] += 1
            connection.execute(
                text(
                    """
                    UPDATE questions
                    SET sequence = :sequence,
                        question_type = COALESCE(question_type, 'mcq'),
                        difficulty = COALESCE(difficulty, 'medium')
                    WHERE id = :id
                    """
                ),
                {"id": row["id"], "sequence": per_scope_sequence[scope]},
            )


def migrate_user_lesson_progress() -> None:
    create_new_tables_if_needed()
    if "user_progress" not in inspect(engine).get_table_names():
        return
    with engine.begin() as connection:
        source_columns = {col["name"] for col in inspect(engine).get_columns("user_progress")}
        lesson_id_column = "sublevel_id" if "sublevel_id" in source_columns else "lesson_id"
        hint_usage_column = "hint_usage" if "hint_usage" in source_columns else "remediation_count"
        source_rows = [
            dict(row)
            for row in connection.execute(
                text(
                    f"""
                    SELECT id, user_id, {lesson_id_column} AS lesson_id, status, current_level,
                           last_score, attempts, mastery_status, {hint_usage_column} AS hint_usage,
                           confidence, question_history
                    FROM user_progress
                    ORDER BY id
                    """
                )
            ).mappings()
        ]
        missing_user_ids = sorted({row["user_id"] for row in source_rows} - set(
            connection.execute(text("SELECT id FROM users")).scalars().all()
        ))
        for user_id in missing_user_ids:
            connection.execute(
                text(
                    """
                    INSERT INTO users (id, username, email, password_hash, session_token, created_at)
                    VALUES (:id, :username, :email, :password_hash, NULL, CURRENT_TIMESTAMP)
                    ON CONFLICT (id) DO NOTHING
                    """
                ),
                {
                    "id": user_id,
                    "username": f"legacy_user_{user_id}",
                    "email": f"legacy-user-{user_id}@example.invalid",
                    "password_hash": "legacy-migrated-account",
                },
            )
        for row in source_rows:
            status = row["status"] or "locked"
            normalized_status = "completed" if status == "mastered" else status
            read_completed = normalized_status in {"learning", "quiz_active", "completed", "continue_check", "reteach", "retry_choice", "mastered"}
            quiz_unlocked = normalized_status in {"quiz_active", "completed", "continue_check", "reteach", "retry_choice", "mastered"}
            quiz_completed = normalized_status in {"completed", "mastered"}
            mastery_status = row["mastery_status"] or "not_started"
            question_history = row["question_history"]
            if not isinstance(question_history, list):
                question_history = [question_history] if question_history else []
            connection.execute(
                text(
                    """
                    INSERT INTO user_lesson_progress (
                        id, user_id, lesson_id, status, current_level, read_completed, quiz_unlocked,
                        quiz_completed, last_score, best_score, attempts, mastery_status, hint_usage,
                        confidence, question_history, updated_at
                    ) VALUES (
                        :id, :user_id, :lesson_id, :status, :current_level, :read_completed,
                        :quiz_unlocked, :quiz_completed, :last_score, :best_score, :attempts,
                        :mastery_status, :hint_usage, :confidence, CAST(:question_history AS JSONB),
                        CURRENT_TIMESTAMP
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        user_id = EXCLUDED.user_id,
                        lesson_id = EXCLUDED.lesson_id,
                        status = EXCLUDED.status,
                        current_level = EXCLUDED.current_level,
                        read_completed = EXCLUDED.read_completed,
                        quiz_unlocked = EXCLUDED.quiz_unlocked,
                        quiz_completed = EXCLUDED.quiz_completed,
                        last_score = EXCLUDED.last_score,
                        best_score = EXCLUDED.best_score,
                        attempts = EXCLUDED.attempts,
                        mastery_status = EXCLUDED.mastery_status,
                        hint_usage = EXCLUDED.hint_usage,
                        confidence = EXCLUDED.confidence,
                        question_history = EXCLUDED.question_history,
                        updated_at = EXCLUDED.updated_at
                    """
                ),
                {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "lesson_id": row["lesson_id"],
                    "status": normalized_status,
                    "current_level": row["current_level"] or "standard",
                    "read_completed": read_completed,
                    "quiz_unlocked": quiz_unlocked,
                    "quiz_completed": quiz_completed,
                    "last_score": row["last_score"],
                    "best_score": row["last_score"],
                    "attempts": row["attempts"] or 0,
                    "mastery_status": mastery_status,
                    "hint_usage": row["hint_usage"] or 0,
                    "confidence": row["confidence"] or 0,
                    "question_history": json.dumps(question_history),
                },
            )


def migrate_user_state() -> None:
    with engine.begin() as connection:
        columns = {col["name"] for col in inspect(engine).get_columns("user_state")}
        if "current_sublevel_id" in columns and "current_lesson_id" not in columns:
            connection.execute(text("ALTER TABLE user_state RENAME COLUMN current_sublevel_id TO current_lesson_id"))
            columns.discard("current_sublevel_id")
            columns.add("current_lesson_id")
        for ddl in (
            ("current_course_id", "INTEGER"),
            ("current_module_id", "INTEGER"),
            ("current_topic_id", "INTEGER"),
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ):
            if ddl[0] not in columns:
                connection.execute(text(f"ALTER TABLE user_state ADD COLUMN {ddl[0]} {ddl[1]}"))
                columns.add(ddl[0])
        connection.execute(
            text(
                """
                UPDATE user_state us
                SET current_topic_id = l.topic_id,
                    current_module_id = t.module_id,
                    current_course_id = m.course_id
                FROM lessons l
                JOIN topics t ON t.id = l.topic_id
                JOIN modules m ON m.id = t.module_id
                WHERE us.current_lesson_id = l.id
                """
            )
        )
        if "current_module" in columns:
            connection.execute(
                text(
                    """
                    UPDATE user_state us
                    SET current_module_id = m.id
                    FROM modules m
                    WHERE us.current_module_id IS NULL AND lower(us.current_module) = lower(m.title)
                    """
                )
            )
        if "current_course" in columns:
            connection.execute(
                text(
                    """
                    UPDATE user_state us
                    SET current_course_id = c.id
                    FROM courses c
                    WHERE us.current_course_id IS NULL AND lower(us.current_course) = lower(c.title)
                    """
                )
            )
        connection.execute(text("UPDATE user_state SET current_level = COALESCE(current_level, 'standard')"))
        connection.execute(text("UPDATE user_state SET updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP)"))
        # Drop legacy string columns only after mapping.
        if "current_course" in columns:
            connection.execute(text("ALTER TABLE user_state DROP COLUMN current_course"))
            columns.discard("current_course")
        if "current_module" in columns:
            connection.execute(text("ALTER TABLE user_state DROP COLUMN current_module"))
            columns.discard("current_module")
        if "attempt_count" in columns:
            connection.execute(text("ALTER TABLE user_state DROP COLUMN attempt_count"))
            columns.discard("attempt_count")
        if "last_score" in columns:
            connection.execute(text("ALTER TABLE user_state DROP COLUMN last_score"))
            columns.discard("last_score")
        if "mastery_status" in columns:
            connection.execute(text("ALTER TABLE user_state DROP COLUMN mastery_status"))
            columns.discard("mastery_status")


def drop_legacy_topic_columns() -> None:
    with engine.begin() as connection:
        columns = {col["name"] for col in inspect(engine).get_columns("topics")}
        for column_name in ("module", "course", "position"):
            if column_name in columns:
                connection.execute(text(f"ALTER TABLE topics DROP COLUMN {column_name}"))


def ensure_indexes() -> None:
    with engine.begin() as connection:
        statements = [
            "CREATE INDEX IF NOT EXISTS ix_modules_course_sequence ON modules(course_id, sequence)",
            "CREATE INDEX IF NOT EXISTS ix_topics_module_sequence ON topics(module_id, sequence)",
            "CREATE INDEX IF NOT EXISTS ix_lessons_topic_sequence ON lessons(topic_id, sequence)",
            "CREATE INDEX IF NOT EXISTS ix_labs_lesson_sequence ON labs(lesson_id, sequence)",
            "CREATE INDEX IF NOT EXISTS ix_lab_tasks_lab_sequence ON lab_tasks(lab_id, sequence)",
            "CREATE INDEX IF NOT EXISTS ix_lab_sessions_user_lab ON lab_sessions(user_id, lab_id)",
            "CREATE INDEX IF NOT EXISTS ix_lesson_contents_lesson_level_sequence ON lesson_contents(lesson_id, level, sequence)",
            "CREATE INDEX IF NOT EXISTS ix_practice_exercises_lesson_sequence ON practice_exercises(lesson_id, sequence)",
            "CREATE INDEX IF NOT EXISTS ix_questions_lesson_level_sequence ON questions(lesson_id, level, sequence)",
            "CREATE INDEX IF NOT EXISTS ix_user_lesson_progress_user_lesson ON user_lesson_progress(user_id, lesson_id)",
            "CREATE INDEX IF NOT EXISTS ix_user_sessions_user_id ON user_sessions(user_id)",
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_user_sessions_session_token ON user_sessions(session_token)",
            "CREATE INDEX IF NOT EXISTS ix_user_state_user_id ON user_state(user_id)",
        ]
        for statement in statements:
            connection.execute(text(statement))


def ensure_foreign_keys() -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                DO $$
                DECLARE
                    stale_constraint text;
                BEGIN
                    FOR stale_constraint IN
                        SELECT con.conname
                        FROM pg_constraint con
                        JOIN pg_attribute att
                            ON att.attrelid = con.conrelid
                           AND att.attnum = ANY(con.conkey)
                        WHERE con.conrelid = 'questions'::regclass
                          AND con.contype = 'f'
                          AND att.attname = 'lesson_id'
                          AND con.confrelid <> 'lessons'::regclass
                    LOOP
                        EXECUTE format('ALTER TABLE questions DROP CONSTRAINT %I', stale_constraint);
                    END LOOP;

                    IF NOT EXISTS (
                        SELECT 1
                        FROM pg_constraint
                        WHERE conrelid = 'questions'::regclass
                          AND contype = 'f'
                          AND conname = 'questions_lesson_id_fkey'
                    ) THEN
                        ALTER TABLE questions
                        ADD CONSTRAINT questions_lesson_id_fkey
                        FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE;
                    END IF;

                    UPDATE user_state us SET current_course_id = NULL
                    WHERE current_course_id IS NOT NULL
                      AND NOT EXISTS (SELECT 1 FROM courses c WHERE c.id = us.current_course_id);
                    UPDATE user_state us SET current_module_id = NULL
                    WHERE current_module_id IS NOT NULL
                      AND NOT EXISTS (SELECT 1 FROM modules m WHERE m.id = us.current_module_id);
                    UPDATE user_state us SET current_topic_id = NULL
                    WHERE current_topic_id IS NOT NULL
                      AND NOT EXISTS (SELECT 1 FROM topics t WHERE t.id = us.current_topic_id);
                    UPDATE user_state us SET current_lesson_id = NULL
                    WHERE current_lesson_id IS NOT NULL
                      AND NOT EXISTS (SELECT 1 FROM lessons l WHERE l.id = us.current_lesson_id);

                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint
                        WHERE conrelid = 'user_state'::regclass
                          AND contype = 'f'
                          AND conname = 'user_state_user_id_fkey'
                    ) THEN
                        ALTER TABLE user_state
                        ADD CONSTRAINT user_state_user_id_fkey
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
                    END IF;
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint
                        WHERE conrelid = 'user_state'::regclass
                          AND contype = 'f'
                          AND conname = 'user_state_current_course_id_fkey'
                    ) THEN
                        ALTER TABLE user_state
                        ADD CONSTRAINT user_state_current_course_id_fkey
                        FOREIGN KEY (current_course_id) REFERENCES courses(id) ON DELETE SET NULL;
                    END IF;
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint
                        WHERE conrelid = 'user_state'::regclass
                          AND contype = 'f'
                          AND conname = 'user_state_current_module_id_fkey'
                    ) THEN
                        ALTER TABLE user_state
                        ADD CONSTRAINT user_state_current_module_id_fkey
                        FOREIGN KEY (current_module_id) REFERENCES modules(id) ON DELETE SET NULL;
                    END IF;
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint
                        WHERE conrelid = 'user_state'::regclass
                          AND contype = 'f'
                          AND conname = 'user_state_current_topic_id_fkey'
                    ) THEN
                        ALTER TABLE user_state
                        ADD CONSTRAINT user_state_current_topic_id_fkey
                        FOREIGN KEY (current_topic_id) REFERENCES topics(id) ON DELETE SET NULL;
                    END IF;
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint
                        WHERE conrelid = 'user_state'::regclass
                          AND contype = 'f'
                          AND conname = 'user_state_current_lesson_id_fkey'
                    ) THEN
                        ALTER TABLE user_state
                        ADD CONSTRAINT user_state_current_lesson_id_fkey
                        FOREIGN KEY (current_lesson_id) REFERENCES lessons(id) ON DELETE SET NULL;
                    END IF;
                END $$;
                """
            )
        )


def sync_serial_sequences() -> None:
    tables = (
        "users",
        "courses",
        "modules",
        "topics",
        "lessons",
        "labs",
        "lab_tasks",
        "lab_sessions",
        "lesson_contents",
        "practice_exercises",
        "questions",
        "user_lesson_progress",
        "user_sessions",
        "user_state",
    )
    with engine.begin() as connection:
        for table_name in tables:
            connection.execute(
                text(
                    f"""
                    SELECT setval(
                        pg_get_serial_sequence('{table_name}', 'id'),
                        COALESCE((SELECT MAX(id) FROM {table_name}), 0) + 1,
                        false
                    )
                    """
                )
            )


def verify_migration() -> list[str]:
    inspector = inspect(engine)
    issues: list[str] = []

    with engine.connect() as connection:
        # These tables describe the stable course hierarchy created by the
        # migration. Lesson content, questions, and user progress are mutable
        # after startup, so backup row-id checks for them would block normal
        # generated-content imports and development resets.
        legacy_presence_checks = [
            ("courses", "backup_courses", "courses"),
            ("modules", "backup_modules", "modules"),
            ("topics", "backup_topics", "topics"),
            ("lessons", "backup_sublevels", "lessons"),
        ]
        for label, backup_table, target_table in legacy_presence_checks:
            backup_exists = connection.execute(text("SELECT to_regclass(:table_name)"), {"table_name": backup_table}).scalar_one()
            if not backup_exists:
                continue
            missing_count = connection.execute(
                text(
                    f"""
                    SELECT COUNT(*)
                    FROM {backup_table} backup
                    LEFT JOIN {target_table} target ON target.id = backup.id
                    WHERE target.id IS NULL
                    """
                )
            ).scalar_one()
            if missing_count:
                issues.append(f"Missing migrated legacy rows for {label}: {missing_count}")

        integrity_checks = {
            "lessons topic_id": "SELECT COUNT(*) FROM lessons l LEFT JOIN topics t ON t.id = l.topic_id WHERE t.id IS NULL",
            "topics module_id": "SELECT COUNT(*) FROM topics t LEFT JOIN modules m ON m.id = t.module_id WHERE m.id IS NULL",
            "modules course_id": "SELECT COUNT(*) FROM modules m LEFT JOIN courses c ON c.id = m.course_id WHERE c.id IS NULL",
            "questions lesson_id": "SELECT COUNT(*) FROM questions q LEFT JOIN lessons l ON l.id = q.lesson_id WHERE l.id IS NULL",
            "lesson_contents lesson_id": "SELECT COUNT(*) FROM lesson_contents lc LEFT JOIN lessons l ON l.id = lc.lesson_id WHERE l.id IS NULL",
            "user_lesson_progress refs": "SELECT COUNT(*) FROM user_lesson_progress ulp LEFT JOIN users u ON u.id = ulp.user_id LEFT JOIN lessons l ON l.id = ulp.lesson_id WHERE u.id IS NULL OR l.id IS NULL",
            "duplicate lesson slugs": "SELECT COUNT(*) FROM (SELECT topic_id, slug FROM lessons GROUP BY topic_id, slug HAVING COUNT(*) > 1) d",
            "duplicate topic slugs": "SELECT COUNT(*) FROM (SELECT module_id, slug FROM topics GROUP BY module_id, slug HAVING COUNT(*) > 1) d",
            "duplicate module slugs": "SELECT COUNT(*) FROM (SELECT course_id, slug FROM modules GROUP BY course_id, slug HAVING COUNT(*) > 1) d",
        }
        for label, sql in integrity_checks.items():
            failures = connection.execute(text(sql)).scalar_one()
            if failures:
                issues.append(f"Integrity check failed for {label}: {failures}")

    _ = inspector
    return issues


def migrate_database() -> None:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    if not existing_tables:
        return

    for table_name in ("courses", "modules", "topics", "sublevels", "explanations", "questions", "user_progress", "user_state", "users"):
        if table_name in existing_tables:
            ensure_backup_table(table_name)

    migrate_courses_modules_topics_users()
    migrate_lessons()
    migrate_lesson_contents()
    migrate_questions()
    migrate_user_lesson_progress()
    migrate_user_state()
    ensure_foreign_keys()
    ensure_indexes()
    sync_serial_sequences()

    issues = verify_migration()
    if issues:
        raise RuntimeError("Lesson migration verification failed:\n" + "\n".join(issues))

    drop_legacy_topic_columns()
