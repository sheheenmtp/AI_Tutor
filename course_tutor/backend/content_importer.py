import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError

from backend.db import SessionLocal
from backend.models import Lab, LabTask, Lesson, LessonContent, Module, PracticeExercise, Question, Topic


REQUIRED_LEVELS = ("standard", "layman", "eli10")
SAFE_COMMANDS = {
    "cat",
    "cd",
    "date",
    "echo",
    "head",
    "id",
    "ls",
    "mkdir",
    "printf",
    "ps",
    "pwd",
    "touch",
    "whoami",
}
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PROJECT_ROOT = Path(__file__).resolve().parent.parent
HARDCODED_IMPORT_PATHS = [
    PROJECT_ROOT / "Data" / "generated",
]


class ContentImportError(ValueError):
    pass


def slugify(value: str, fallback: str) -> str:
    lowered = (value or "").strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or fallback


def as_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def as_json_list(value: Any) -> list[Any]:
    if not isinstance(value, list):
        return []
    return value


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContentImportError(f"{label} must be an object")
    return value


def require_non_empty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContentImportError(f"{label} must be a non-empty string")
    return value.strip()


def validate_slug(value: str, label: str) -> None:
    if not SLUG_RE.fullmatch(value):
        raise ContentImportError(f"{label} must be lowercase kebab-case, got {value!r}")


def validate_allowed_commands(commands: Any, label: str) -> list[str]:
    if not isinstance(commands, list) or not commands:
        raise ContentImportError(f"{label} must be a non-empty list")
    normalized = []
    for command in commands:
        if not isinstance(command, str) or not command.strip():
            raise ContentImportError(f"{label} contains a non-string command")
        command_name = command.strip()
        if command_name not in SAFE_COMMANDS:
            raise ContentImportError(
                f"{label} contains unsafe command {command_name!r}. "
                f"Allowed commands: {', '.join(sorted(SAFE_COMMANDS))}"
            )
        normalized.append(command_name)
    return normalized


def validate_questions(questions: Any, level: str) -> list[dict[str, Any]]:
    if not isinstance(questions, list) or len(questions) != 10:
        raise ContentImportError(f"levels.{level}.questions must contain exactly 10 questions")

    normalized = []
    for index, question in enumerate(questions, start=1):
        question = require_object(question, f"levels.{level}.questions[{index}]")
        question_text = require_non_empty_string(question.get("question"), f"levels.{level}.questions[{index}].question")
        options = question.get("options")
        if not isinstance(options, list) or len(options) != 4 or not all(isinstance(option, str) and option.strip() for option in options):
            raise ContentImportError(f"levels.{level}.questions[{index}].options must contain exactly 4 non-empty strings")
        options = [option.strip() for option in options]
        answer = require_non_empty_string(question.get("answer"), f"levels.{level}.questions[{index}].answer")
        if answer not in options:
            raise ContentImportError(f"levels.{level}.questions[{index}].answer must exactly match one option")

        normalized.append(
            {
                "question": question_text,
                "options": options,
                "answer": answer,
                "explanation": question.get("explanation") or None,
                "difficulty": question.get("difficulty") or "medium",
            }
        )
    return normalized


def validate_level(level_data: Any, level: str) -> dict[str, Any]:
    level_data = require_object(level_data, f"levels.{level}")
    explanation = require_non_empty_string(level_data.get("explanation"), f"levels.{level}.explanation")
    questions = validate_questions(level_data.get("questions"), level)
    return {"explanation": explanation, "questions": questions}


def validate_practice_exercise(value: Any, lesson_title: str) -> dict[str, Any] | None:
    if value is None:
        return None

    exercise = require_object(value, "lesson.practice_exercise")
    allowed_commands = validate_allowed_commands(exercise.get("allowed_commands"), "lesson.practice_exercise.allowed_commands")
    starter_code = require_non_empty_string(exercise.get("starter_code"), "lesson.practice_exercise.starter_code")
    expected_output = exercise.get("expected_output") or None
    if isinstance(expected_output, str) and len(expected_output.strip()) > 2:
        if expected_output.strip().lower() in starter_code.lower():
            raise ContentImportError("lesson.practice_exercise.starter_code appears to contain the expected answer")

    title = exercise.get("title") or f"Practice: {lesson_title}"
    prompt = exercise.get("prompt") or exercise.get("task")

    return {
        "title": require_non_empty_string(title, "lesson.practice_exercise.title"),
        "prompt": require_non_empty_string(prompt, "lesson.practice_exercise.prompt"),
        "starter_code": starter_code,
        "expected_output": expected_output,
        "allowed_commands": allowed_commands,
        "is_required": bool(exercise.get("is_required", False)),
    }


def validate_lab(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None

    lab = require_object(value, "lesson.lab")
    tasks = lab.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ContentImportError("lesson.lab.tasks must be a non-empty list when lab is provided")

    normalized_tasks = []
    for index, task in enumerate(tasks, start=1):
        task = require_object(task, f"lesson.lab.tasks[{index}]")
        normalized_tasks.append(
            {
                "title": require_non_empty_string(task.get("title"), f"lesson.lab.tasks[{index}].title"),
                "instruction": require_non_empty_string(task.get("instruction"), f"lesson.lab.tasks[{index}].instruction"),
                "starter_code": require_non_empty_string(task.get("starter_code"), f"lesson.lab.tasks[{index}].starter_code"),
                "expected_output": task.get("expected_output") or None,
                "allowed_commands": validate_allowed_commands(
                    task.get("allowed_commands"),
                    f"lesson.lab.tasks[{index}].allowed_commands",
                ),
                "validation": task.get("validation") if isinstance(task.get("validation"), dict) else None,
            }
        )

    return {
        "title": require_non_empty_string(lab.get("title"), "lesson.lab.title"),
        "description": require_non_empty_string(lab.get("description"), "lesson.lab.description"),
        "sequence": int(lab.get("sequence") or 1),
        "is_required": bool(lab.get("is_required", False)),
        "tasks": normalized_tasks,
    }


def validate_payload(payload: Any, source: Path) -> dict[str, Any]:
    payload = require_object(payload, str(source))
    topic_slug = require_non_empty_string(payload.get("topic_slug"), "topic_slug")
    validate_slug(topic_slug, "topic_slug")

    module_slug = payload.get("module_slug")
    if module_slug is not None:
        module_slug = require_non_empty_string(module_slug, "module_slug")
        validate_slug(module_slug, "module_slug")

    lesson = require_object(payload.get("lesson"), "lesson")
    title = require_non_empty_string(lesson.get("title"), "lesson.title")
    lesson_slug = lesson.get("slug") or slugify(title, "lesson")
    validate_slug(lesson_slug, "lesson.slug")

    levels = require_object(lesson.get("levels"), "lesson.levels")
    missing_levels = [level for level in REQUIRED_LEVELS if level not in levels]
    if missing_levels:
        raise ContentImportError(f"lesson.levels is missing: {', '.join(missing_levels)}")

    normalized_levels = {level: validate_level(levels[level], level) for level in REQUIRED_LEVELS}

    return {
        "topic_slug": topic_slug,
        "module_slug": module_slug,
        "lesson": {
            "title": title,
            "slug": lesson_slug,
            "sequence": int(lesson.get("sequence") or 1),
            "lesson_type": lesson.get("lesson_type") or "concept",
            "difficulty": lesson.get("difficulty") or "beginner",
            "objective": lesson.get("objective") or None,
            "practice_task": lesson.get("practice_task") or None,
            "common_confusions": as_json_list(lesson.get("common_confusions")),
            "examples": as_json_list(lesson.get("examples")),
            "tags": as_string_list(lesson.get("tags")),
            "levels": normalized_levels,
            "practice_exercise": validate_practice_exercise(lesson.get("practice_exercise"), title),
            "lab": validate_lab(lesson.get("lab")),
            "raw_json": payload,
        },
    }


def load_payload(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            raw_payload = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ContentImportError(f"{path}: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc

    return validate_payload(raw_payload, path)


def discover_json_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(sorted(path.rglob("*.json")))
        elif path.is_file():
            files.append(path)
        else:
            raise ContentImportError(f"{path} does not exist")
    return sorted(files)


def find_topic(db, topic_slug: str, module_slug: str | None) -> Topic:
    statement = select(Topic).where(Topic.slug == topic_slug)
    if module_slug:
        statement = statement.join(Module).where(Module.slug == module_slug)

    topics = db.execute(statement).scalars().all()
    if not topics:
        if module_slug:
            raise ContentImportError(f"No topic found for topic_slug={topic_slug!r}, module_slug={module_slug!r}")
        raise ContentImportError(f"No topic found for topic_slug={topic_slug!r}")
    if len(topics) > 1:
        raise ContentImportError(
            f"Multiple topics found for topic_slug={topic_slug!r}; add module_slug to the JSON file"
        )
    return topics[0]


def upsert_lesson(db, topic: Topic, lesson_data: dict[str, Any]) -> Lesson:
    lesson = db.execute(
        select(Lesson).where(
            Lesson.topic_id == topic.id,
            Lesson.slug == lesson_data["slug"],
        )
    ).scalar_one_or_none()

    if not lesson:
        lesson = Lesson(topic_id=topic.id, slug=lesson_data["slug"])
        db.add(lesson)

    lesson.title = lesson_data["title"]
    lesson.sequence = lesson_data["sequence"]
    lesson.lesson_type = lesson_data["lesson_type"]
    lesson.difficulty = lesson_data["difficulty"]
    lesson.objective = lesson_data["objective"]
    lesson.practice_task = lesson_data["practice_task"]
    lesson.common_confusions = lesson_data["common_confusions"]
    lesson.examples = lesson_data["examples"]
    lesson.tags = lesson_data["tags"]
    lesson.raw_json = lesson_data["raw_json"]
    db.flush()
    return lesson


def replace_lesson_contents(db, lesson: Lesson, levels: dict[str, Any]) -> None:
    db.execute(
        delete(LessonContent).where(
            LessonContent.lesson_id == lesson.id,
            LessonContent.content_type == "explanation",
        )
    )
    for level_name, level_data in levels.items():
        db.add(
            LessonContent(
                lesson_id=lesson.id,
                level=level_name,
                content_type="explanation",
                title=None,
                content=level_data["explanation"],
                sequence=1,
            )
        )


def replace_questions(db, lesson: Lesson, levels: dict[str, Any]) -> None:
    db.execute(delete(Question).where(Question.lesson_id == lesson.id))
    for level_name, level_data in levels.items():
        for index, question_data in enumerate(level_data["questions"], start=1):
            db.add(
                Question(
                    lesson_id=lesson.id,
                    level=level_name,
                    question_type="mcq",
                    question=question_data["question"],
                    options=question_data["options"],
                    correct_answer=question_data["answer"],
                    explanation=question_data["explanation"],
                    difficulty=question_data["difficulty"],
                    sequence=index,
                )
            )


def upsert_practice_exercise(db, lesson: Lesson, exercise_data: dict[str, Any] | None) -> None:
    if exercise_data is None:
        db.execute(delete(PracticeExercise).where(PracticeExercise.lesson_id == lesson.id))
        return

    exercise = db.execute(
        select(PracticeExercise).where(
            PracticeExercise.lesson_id == lesson.id,
            PracticeExercise.sequence == 1,
        )
    ).scalar_one_or_none()

    if not exercise:
        exercise = PracticeExercise(lesson_id=lesson.id, sequence=1)
        db.add(exercise)

    exercise.title = exercise_data["title"]
    exercise.prompt = exercise_data["prompt"]
    exercise.starter_code = exercise_data["starter_code"]
    exercise.expected_output = exercise_data["expected_output"]
    exercise.allowed_commands = exercise_data["allowed_commands"]
    exercise.is_required = exercise_data["is_required"]


def replace_lab(db, lesson: Lesson, lab_data: dict[str, Any] | None) -> None:
    db.execute(delete(Lab).where(Lab.lesson_id == lesson.id))
    if lab_data is None:
        return

    lab = Lab(
        lesson_id=lesson.id,
        title=lab_data["title"],
        description=lab_data["description"],
        sequence=lab_data["sequence"],
        is_required=lab_data["is_required"],
    )
    db.add(lab)
    db.flush()

    for index, task_data in enumerate(lab_data["tasks"], start=1):
        db.add(
            LabTask(
                lab_id=lab.id,
                title=task_data["title"],
                instruction=task_data["instruction"],
                starter_code=task_data["starter_code"],
                expected_output=task_data["expected_output"],
                allowed_commands=task_data["allowed_commands"],
                validation=task_data["validation"],
                sequence=index,
            )
        )


def import_payload(db, payload: dict[str, Any]) -> str:
    topic = find_topic(db, payload["topic_slug"], payload["module_slug"])
    lesson_data = payload["lesson"]
    lesson = upsert_lesson(db, topic, lesson_data)
    replace_lesson_contents(db, lesson, lesson_data["levels"])
    replace_questions(db, lesson, lesson_data["levels"])
    upsert_practice_exercise(db, lesson, lesson_data["practice_exercise"])
    replace_lab(db, lesson, lesson_data["lab"])
    return f"{topic.slug}/{lesson.slug}"


def import_files(paths: list[Path], dry_run: bool = False) -> list[str]:
    json_files = discover_json_files(paths)
    if not json_files:
        raise ContentImportError("No JSON files found")

    imported: list[str] = []
    with SessionLocal() as db:
        for path in json_files:
            try:
                payload = load_payload(path)
                imported.append(import_payload(db, payload))
            except ContentImportError as exc:
                raise ContentImportError(f"{path}: {exc}") from exc

        if dry_run:
            db.rollback()
        else:
            db.commit()

    return imported


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Import one-subtopic generated lesson JSON into the existing course database."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Optional generated JSON file(s) or directories. Defaults to Data/generated.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and prepare imports, then roll back without writing changes.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    paths = args.paths or HARDCODED_IMPORT_PATHS

    try:
        imported = import_files(paths, dry_run=args.dry_run)
    except ContentImportError as exc:
        print(f"Import failed: {exc}", file=sys.stderr)
        return 1
    except SQLAlchemyError as exc:
        print(f"Import failed: database error: {exc}", file=sys.stderr)
        return 1

    mode = "Validated" if args.dry_run else "Imported"
    for item in imported:
        print(f"{mode}: {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
