import json
import os
import re

from sqlalchemy import select

from backend.db import SessionLocal
from backend.models import Course, Lab, LabTask, Lesson, LessonContent, Module, PracticeExercise, Question, Topic

COURSE_TITLE = "Linux Userspace Foundations"
MODULE_TITLE = "What Userspace Is"
TOPIC_TITLE = "Introduction to Userspace"
COURSE_SLUG = "linux-userspace-foundations"
MODULE_SLUG = "what-userspace-is"
TOPIC_SLUG = "introduction-to-userspace"

DEFAULT_ALLOWED_COMMANDS = ["echo", "pwd", "id", "ps", "head", "grep", "ls"]
PRACTICE_EXERCISES = {
    "meaning-of-userspace": {
        "title": "Print a userspace clue",
        "prompt": "Use Bash to print a short sentence that includes the word userspace.",
        "starter_code": "# Write an echo command that includes the required word\n",
        "expected_output": "userspace",
        "allowed_commands": ["echo"],
    },
    "ordinary-software-world": {
        "title": "See your current location",
        "prompt": "Run a command that prints the current working directory.",
        "starter_code": "# Print the current working directory\n",
        "expected_output": "/",
        "allowed_commands": ["pwd"],
    },
    "where-apps-run": {
        "title": "Identify the current user id",
        "prompt": "Run a command that prints the numeric user id for this Bash process.",
        "starter_code": "# Print the numeric user id\n",
        "expected_output": "",
        "allowed_commands": ["id"],
    },
    "userspace-as-execution-area": {
        "title": "List visible files",
        "prompt": "Run a command that lists files in the current directory.",
        "starter_code": "# List files in the current directory\n",
        "expected_output": "",
        "allowed_commands": ["ls"],
    },
    "not-kernel-internals": {
        "title": "Describe the boundary",
        "prompt": "Print a sentence that says apps ask the kernel for protected work.",
        "starter_code": "# Write an echo command that mentions the required idea\n",
        "expected_output": "kernel",
        "allowed_commands": ["echo"],
    },
    "above-syscall-boundary": {
        "title": "Filter process output",
        "prompt": "Use ps and head to show the first few running processes.",
        "starter_code": "# Use ps and head together\n",
        "expected_output": "PID",
        "allowed_commands": ["ps", "head"],
    },
    "visible-and-invisible-software": {
        "title": "Find a shell process",
        "prompt": "Use ps and grep to look for shell-related processes.",
        "starter_code": "# Use ps and grep together\n",
        "expected_output": "",
        "allowed_commands": ["ps", "grep"],
    },
    "why-userspace-matters": {
        "title": "Summarize userspace safety",
        "prompt": "Print a short sentence about userspace helping isolate normal apps.",
        "starter_code": "# Write an echo command that includes the required word\n",
        "expected_output": "isolate",
        "allowed_commands": ["echo"],
    },
}

LABS_BY_LESSON = {
    "why-userspace-matters": {
        "title": "Lab: Basic Linux Observation Commands",
        "description": (
            "Use a small set of safe Linux commands to inspect the running Bash environment, "
            "connect lesson ideas to real command output, and practice reading terminal results."
        ),
        "sequence": 1,
        "is_required": False,
        "tasks": [
            {
                "title": "Find Where Bash Starts",
                "instruction": "Print the current working directory and inspect the path returned by the runner.",
                "starter_code": "# Print the current working directory\n",
                "expected_output": "/",
                "allowed_commands": ["pwd"],
            },
            {
                "title": "List the Workspace",
                "instruction": "List the visible files and directories in the current working directory.",
                "starter_code": "# List files and directories here\n",
                "expected_output": "",
                "allowed_commands": ["ls"],
            },
            {
                "title": "Identify the Process User",
                "instruction": "Print the numeric user id for the Bash process.",
                "starter_code": "# Print only the numeric user id\n",
                "expected_output": "",
                "allowed_commands": ["id"],
            },
            {
                "title": "Read Process Output",
                "instruction": "Show the first few rows from the process list.",
                "starter_code": "# Show a short process list\n",
                "expected_output": "PID",
                "allowed_commands": ["ps", "head"],
            },
            {
                "title": "Filter for Shell Processes",
                "instruction": "Filter process output to look for shell-related process names.",
                "starter_code": "# Filter process output for shell names\n",
                "expected_output": "",
                "allowed_commands": ["ps", "grep"],
            },
        ],
    }
}


def slugify(value: str, fallback: str) -> str:
    lowered = (value or "").strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or fallback


def initialize_data() -> None:
    data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Data", "topic1.json"))
    if not os.path.exists(data_path):
        return

    with open(data_path, "r", encoding="utf-8") as handle:
        topics = json.load(handle)

    if not topics:
        return

    with SessionLocal() as db:
        course_model = db.execute(select(Course).where(Course.slug == COURSE_SLUG)).scalar_one_or_none()
        if not course_model:
            course_model = Course(
                title=COURSE_TITLE,
                slug=COURSE_SLUG,
                sequence=1,
                is_published=True,
            )
            db.add(course_model)
            db.flush()
        else:
            course_model.title = COURSE_TITLE
            course_model.sequence = 1
            course_model.is_published = True

        module_model = db.execute(
            select(Module).where(Module.slug == MODULE_SLUG, Module.course_id == course_model.id)
        ).scalar_one_or_none()
        if not module_model:
            module_model = Module(
                title=MODULE_TITLE,
                slug=MODULE_SLUG,
                course_id=course_model.id,
                sequence=1,
            )
            db.add(module_model)
            db.flush()
        else:
            module_model.title = MODULE_TITLE
            module_model.sequence = 1

        topic_model = db.execute(
            select(Topic).where(Topic.slug == TOPIC_SLUG, Topic.module_id == module_model.id)
        ).scalar_one_or_none()
        if not topic_model:
            topic_model = Topic(
                title=TOPIC_TITLE,
                slug=TOPIC_SLUG,
                module_id=module_model.id,
                sequence=1,
            )
            db.add(topic_model)
            db.flush()
        else:
            topic_model.title = TOPIC_TITLE
            topic_model.sequence = 1

        for index, topic in enumerate(topics, start=1):
            title = topic["topic_name"]
            lesson_slug = topic.get("slug") or slugify(title, f"lesson-{index}")
            lesson = db.execute(
                select(Lesson).where(Lesson.slug == lesson_slug, Lesson.topic_id == topic_model.id)
            ).scalar_one_or_none()
            if lesson and (lesson.objective or (isinstance(lesson.raw_json, dict) and lesson.raw_json.get("topic_slug"))):
                continue
            if not lesson:
                lesson = Lesson(
                    title=title,
                    slug=lesson_slug,
                    topic_id=topic_model.id,
                    sequence=index,
                    raw_json=topic,
                )
                db.add(lesson)
                db.flush()
            else:
                lesson.title = title
                lesson.sequence = index
                lesson.raw_json = topic

            for level_name, level_data in topic.get("levels", {}).items():
                content_model = db.execute(
                    select(LessonContent).where(
                        LessonContent.lesson_id == lesson.id,
                        LessonContent.level == level_name,
                        LessonContent.content_type == "explanation",
                        LessonContent.sequence == 1,
                    )
                ).scalar_one_or_none()
                if content_model:
                    content_model.content = level_data.get("explanation", "")
                else:
                    db.add(
                        LessonContent(
                            lesson_id=lesson.id,
                            level=level_name,
                            content=level_data.get("explanation", ""),
                            sequence=1,
                        )
                    )

                existing_questions = db.execute(
                    select(Question).where(
                        Question.lesson_id == lesson.id,
                        Question.level == level_name,
                    )
                ).scalars().all()
                questions_by_sequence = {question.sequence: question for question in existing_questions}

                for question_index, question_data in enumerate(level_data.get("questions", []), start=1):
                    question_model = questions_by_sequence.get(question_index)
                    if question_model:
                        question_model.question = question_data.get("question", "")
                        question_model.options = question_data.get("options", [])
                        question_model.correct_answer = question_data.get("answer", "")
                    else:
                        db.add(
                            Question(
                                lesson_id=lesson.id,
                                level=level_name,
                                question=question_data.get("question", ""),
                                options=question_data.get("options", []),
                                correct_answer=question_data.get("answer", ""),
                                sequence=question_index,
                            )
                        )

            exercise_data = PRACTICE_EXERCISES.get(
                lesson.slug,
                {
                    "title": "Try a Bash command",
                    "prompt": "Write a simple Bash command and inspect the output.",
                    "starter_code": "# Try a simple allowed command\n",
                    "expected_output": "practice",
                    "allowed_commands": DEFAULT_ALLOWED_COMMANDS,
                },
            )
            exercise = db.execute(
                select(PracticeExercise).where(
                    PracticeExercise.lesson_id == lesson.id,
                    PracticeExercise.sequence == 1,
                )
            ).scalar_one_or_none()
            if exercise:
                exercise.title = exercise_data["title"]
                exercise.prompt = exercise_data["prompt"]
                exercise.starter_code = exercise_data["starter_code"]
                exercise.expected_output = exercise_data["expected_output"]
                exercise.allowed_commands = exercise_data["allowed_commands"]
                exercise.is_required = False
            else:
                db.add(
                    PracticeExercise(
                        lesson_id=lesson.id,
                        title=exercise_data["title"],
                        prompt=exercise_data["prompt"],
                        starter_code=exercise_data["starter_code"],
                        expected_output=exercise_data["expected_output"],
                        allowed_commands=exercise_data["allowed_commands"],
                        sequence=1,
                        is_required=False,
                    )
                )

            lab_data = LABS_BY_LESSON.get(lesson.slug)
            if lab_data:
                lab = db.execute(
                    select(Lab).where(
                        Lab.lesson_id == lesson.id,
                        Lab.sequence == lab_data["sequence"],
                    )
                ).scalar_one_or_none()
                if lab:
                    lab.title = lab_data["title"]
                    lab.description = lab_data["description"]
                    lab.is_required = lab_data["is_required"]
                else:
                    lab = Lab(
                        lesson_id=lesson.id,
                        title=lab_data["title"],
                        description=lab_data["description"],
                        sequence=lab_data["sequence"],
                        is_required=lab_data["is_required"],
                    )
                    db.add(lab)
                    db.flush()

                existing_tasks = db.execute(select(LabTask).where(LabTask.lab_id == lab.id)).scalars().all()
                tasks_by_sequence = {task.sequence: task for task in existing_tasks}

                for task_index, task_data in enumerate(lab_data["tasks"], start=1):
                    task = tasks_by_sequence.get(task_index)
                    if task:
                        task.title = task_data["title"]
                        task.instruction = task_data["instruction"]
                        task.starter_code = task_data["starter_code"]
                        task.expected_output = task_data["expected_output"]
                        task.allowed_commands = task_data["allowed_commands"]
                    else:
                        db.add(
                            LabTask(
                                lab_id=lab.id,
                                title=task_data["title"],
                                instruction=task_data["instruction"],
                                starter_code=task_data["starter_code"],
                                expected_output=task_data["expected_output"],
                                allowed_commands=task_data["allowed_commands"],
                                sequence=task_index,
                            )
                        )

        for lesson in db.execute(select(Lesson)).scalars().all():
            existing_exercise = db.execute(
                select(PracticeExercise).where(
                    PracticeExercise.lesson_id == lesson.id,
                    PracticeExercise.sequence == 1,
                )
            ).scalar_one_or_none()
            if existing_exercise:
                if lesson.slug not in PRACTICE_EXERCISES and existing_exercise.starter_code == 'echo "practice"':
                    existing_exercise.prompt = "Write a simple Bash command and inspect the output."
                    existing_exercise.starter_code = "# Try a simple allowed command\n"
                    existing_exercise.allowed_commands = DEFAULT_ALLOWED_COMMANDS
                continue

            db.add(
                PracticeExercise(
                    lesson_id=lesson.id,
                    title="Try a Bash command",
                    prompt="Write a simple Bash command and inspect the output.",
                    starter_code="# Try a simple allowed command\n",
                    expected_output="practice",
                    allowed_commands=DEFAULT_ALLOWED_COMMANDS,
                    sequence=1,
                    is_required=False,
                )
            )

        db.commit()
