import os
import random
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.db import SessionLocal
from backend.models import (
    Course,
    Lab,
    Lesson,
    LessonContent,
    Module,
    PracticeExercise,
    Question,
    Topic,
    User,
    UserLessonProgress,
    UserState,
)
from backend.routes.auth import get_optional_current_user
from backend.schemas import (
    CourseHierarchyItem,
    LabItem,
    LabTaskItem,
    LessonContentUpdate,
    LessonHierarchyContent,
    LessonHierarchyItem,
    LessonHierarchyQuestion,
    LessonListItem,
    LessonResponse,
    ModuleHierarchyItem,
    NextResponse,
    PracticeExerciseItem,
    QuizQuestion,
    QuizResponse,
    RetryPrompt,
    SubmitRequest,
    SubmitResponse,
    TopicHierarchyItem,
)

router = APIRouter()

LEVELS = ["standard", "layman", "eli10"]
DEFAULT_LEVEL = "standard"
PASS_PERCENTAGE = 100
ANSWER_THRESHOLD = 3
COUNTER_KEY = "_answer_counts"
RETRY_LIMIT = 3
RETRY_COUNT_KEY = "_retry_choice_count"
PENDING_REVIEW_KEY = "_pending_review"
DEV_UNLOCK_ALL_CONTENT = os.getenv("DEV_UNLOCK_ALL_CONTENT", "true").lower() in {"1", "true", "yes", "on"}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def resolve_user_id(explicit_user_id: int | None, current_user: User | None) -> int:
    if current_user:
        return current_user.id
    if explicit_user_id is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return explicit_user_id


def get_lesson_progress(db: Session, user_id: int, lesson_id: int) -> UserLessonProgress | None:
    return db.execute(
        select(UserLessonProgress).where(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.lesson_id == lesson_id,
        )
    ).scalar_one_or_none()


def get_or_create_lesson_progress(db: Session, user_id: int, lesson_id: int) -> UserLessonProgress:
    progress = get_lesson_progress(db, user_id, lesson_id)
    if progress:
        return progress

    progress = UserLessonProgress(
        user_id=user_id,
        lesson_id=lesson_id,
        status="learning",
        current_level=DEFAULT_LEVEL,
        read_completed=True,
        quiz_unlocked=True,
        question_history=[],
    )
    db.add(progress)
    db.flush()
    return progress


def get_user_state(db: Session, user_id: int) -> UserState | None:
    return db.execute(select(UserState).where(UserState.user_id == user_id)).scalar_one_or_none()


def lesson_ordering():
    return (
        select(Lesson)
        .join(Topic, Topic.id == Lesson.topic_id)
        .join(Module, Module.id == Topic.module_id)
        .join(Course, Course.id == Module.course_id)
        .options(
            selectinload(Lesson.topic).selectinload(Topic.module).selectinload(Module.course),
            selectinload(Lesson.labs).selectinload(Lab.tasks),
        )
        .order_by(Course.sequence, Module.sequence, Topic.sequence, Lesson.sequence, Lesson.id)
    )


def get_first_lesson(db: Session) -> Lesson:
    lesson = db.execute(lesson_ordering()).scalars().first()
    if not lesson:
        raise HTTPException(status_code=404, detail="No lessons have been seeded")
    return lesson


def get_or_create_user_state(db: Session, user_id: int) -> UserState:
    state = get_user_state(db, user_id)
    if state:
        return state

    first_lesson = get_first_lesson(db)
    state = UserState(
        user_id=user_id,
        current_course_id=first_lesson.topic.module.course.id,
        current_module_id=first_lesson.topic.module.id,
        current_topic_id=first_lesson.topic.id,
        current_lesson_id=first_lesson.id,
        current_level=DEFAULT_LEVEL,
    )
    db.add(state)
    db.flush()
    return state


def get_lesson_content(db: Session, lesson_id: int, level: str) -> LessonContent | None:
    return db.execute(
        select(LessonContent).where(
            LessonContent.lesson_id == lesson_id,
            LessonContent.level == level,
        ).order_by(LessonContent.sequence, LessonContent.id)
    ).scalars().first()


def get_questions(db: Session, lesson_id: int, level: str) -> List[Question]:
    return db.execute(
        select(Question).where(
            Question.lesson_id == lesson_id,
            Question.level == level,
        ).order_by(Question.sequence, Question.id)
    ).scalars().all()


def get_next_question(db: Session, lesson_id: int, level: str, progress: UserLessonProgress | None) -> Question:
    questions = get_questions(db, lesson_id, level)
    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for this lesson and level")

    history = progress.question_history if progress and progress.question_history else []
    failed_ids: set[int] = set()
    if isinstance(history, dict):
        failed_ids = set(history.get(level, []))
    available = [question for question in questions if question.id not in failed_ids]
    if not available:
        available = questions
    return random.choice(available)


def question_payload(question: Question) -> QuizQuestion:
    shuffled_options = list(question.options)
    random.shuffle(shuffled_options)
    return QuizQuestion(
        question_id=question.id,
        question=question.question,
        options=shuffled_options,
        question_type=question.question_type,
    )


def get_lesson_model(db: Session, lesson_id: int) -> Lesson:
    lesson = db.execute(
        select(Lesson)
        .where(Lesson.id == lesson_id)
        .options(
            selectinload(Lesson.topic).selectinload(Topic.module).selectinload(Module.course),
            selectinload(Lesson.practice_exercises),
            selectinload(Lesson.labs).selectinload(Lab.tasks),
        )
    ).scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


def resolve_lesson_id(db: Session, user_id: int, lesson_id: int | None, sublevel_id: int | None = None) -> int:
    explicit = lesson_id or sublevel_id
    if explicit is not None:
        return explicit
    state = get_or_create_user_state(db, user_id)
    if state.current_lesson_id is None:
        state.current_lesson_id = get_first_lesson(db).id
        db.flush()
    return state.current_lesson_id


def resolve_level(progress: UserLessonProgress | None) -> str:
    return progress.current_level if progress else DEFAULT_LEVEL


def get_next_lesson(db: Session, lesson: Lesson) -> Lesson | None:
    lessons = db.execute(lesson_ordering()).scalars().all()
    for index, item in enumerate(lessons):
        if item.id == lesson.id:
            return lessons[index + 1] if index + 1 < len(lessons) else None
    return None


def level_after_fail(level: str) -> str:
    if level == "standard":
        return "layman"
    if level == "layman":
        return "eli10"
    return "eli10"


def level_after_pass(level: str) -> str:
    if level == "eli10":
        return "layman"
    if level == "layman":
        return "standard"
    return "standard"


def get_adaptive_message(prev_level: str, next_level: str) -> str | None:
    previous = prev_level.upper()
    upcoming = next_level.upper()
    if previous == "STANDARD" and upcoming == "LAYMAN":
        return "Let's break this down in a simpler way before moving forward."
    if previous == "LAYMAN" and upcoming == "ELI10":
        return "Let's look at this with a very simple example to make it clearer."
    if previous == "ELI10":
        return "Let's try another way to understand this concept."
    return None


def answer_counts(progress: UserLessonProgress) -> dict[str, int]:
    history = progress.question_history or []
    if isinstance(history, dict):
        counts = history.get(COUNTER_KEY, {})
    else:
        counts = {}
    return {
        "correct": int(counts.get("correct", 0)),
        "wrong": int(counts.get("wrong", 0)),
    }


def save_answer_counts(progress: UserLessonProgress, correct: int, wrong: int) -> None:
    history = dict(progress.question_history or {}) if isinstance(progress.question_history, dict) else {}
    history[COUNTER_KEY] = {"correct": max(0, correct), "wrong": max(0, wrong)}
    progress.question_history = history


def reset_answer_counts(progress: UserLessonProgress) -> None:
    save_answer_counts(progress, 0, 0)


def get_retry_choice_count(progress: UserLessonProgress) -> int:
    history = progress.question_history or {}
    return int(history.get(RETRY_COUNT_KEY, 0)) if isinstance(history, dict) else 0


def set_retry_choice_count(progress: UserLessonProgress, count: int) -> None:
    history = dict(progress.question_history or {}) if isinstance(progress.question_history, dict) else {}
    history[RETRY_COUNT_KEY] = max(0, count)
    progress.question_history = history


def reset_retry_choice_count(progress: UserLessonProgress) -> None:
    set_retry_choice_count(progress, 0)


def get_pending_review(progress: UserLessonProgress) -> dict[str, str] | None:
    history = progress.question_history or {}
    pending = history.get(PENDING_REVIEW_KEY) if isinstance(history, dict) else None
    return pending if isinstance(pending, dict) else None


def set_pending_review(progress: UserLessonProgress, next_level: str, adaptive_message: str | None) -> None:
    history = dict(progress.question_history or {}) if isinstance(progress.question_history, dict) else {}
    history[PENDING_REVIEW_KEY] = {"next_level": next_level, "adaptive_message": adaptive_message or ""}
    progress.question_history = history


def clear_pending_review(progress: UserLessonProgress) -> None:
    history = dict(progress.question_history or {}) if isinstance(progress.question_history, dict) else {}
    history.pop(PENDING_REVIEW_KEY, None)
    progress.question_history = history


def infer_question_type(question_text: str) -> str:
    lowered = question_text.lower()
    if "why" in lowered or "needs" in lowered or "because" in lowered:
        return "dependency_reasoning"
    if "what happens" in lowered or "command" in lowered or "flow" in lowered:
        return "flow_tracing"
    return "mcq"


def confidence_score(percentage: int, attempts: int) -> int:
    attempt_penalty = min(max(attempts - 1, 0) * 4, 30)
    return max(0, min(100, percentage - attempt_penalty))


def remember_failed_question(progress: UserLessonProgress, level: str, question_id: int) -> None:
    history = dict(progress.question_history or {}) if isinstance(progress.question_history, dict) else {}
    failed_ids = set(history.get(level, []))
    failed_ids.add(question_id)
    history[level] = sorted(failed_ids)
    progress.question_history = history


def base_submit_response(progress: UserLessonProgress) -> SubmitResponse:
    return SubmitResponse(
        score=progress.last_score or 0,
        total=1,
        percentage=0,
        level=progress.current_level,
        status=progress.status,
        interpretation="continue",
        mastered=False,
        next_lesson_id=None,
        needs_hints=False,
        feedback="Continue.",
        can_retry=False,
    )


def build_lesson_content_update(progress: UserLessonProgress, lesson_id: int, content: LessonContent, adaptive_message: str | None) -> LessonContentUpdate:
    _ = progress
    return LessonContentUpdate(
        lesson_id=lesson_id,
        action="LESSON_CONTENT_UPDATE",
        content=content.content,
        adaptive_message=adaptive_message,
    )


def sync_user_state_from_lesson(state: UserState, lesson: Lesson, level: str) -> None:
    state.current_course_id = lesson.topic.module.course.id
    state.current_module_id = lesson.topic.module.id
    state.current_topic_id = lesson.topic.id
    state.current_lesson_id = lesson.id
    state.current_level = level


def resolve_retry_decision(db: Session, lesson: Lesson, progress: UserLessonProgress, decision: str) -> SubmitResponse:
    pending_review = get_pending_review(progress)
    if not pending_review:
        raise HTTPException(status_code=400, detail="No pending retry choice for this lesson")

    choice = decision.strip().lower()
    if choice == "retry_questions":
        set_retry_choice_count(progress, get_retry_choice_count(progress) + 1)
        clear_pending_review(progress)
        progress.status = "quiz_active"
        db.commit()

        selected = get_next_question(db, lesson.id, progress.current_level, progress)
        response = base_submit_response(progress)
        response.can_retry = True
        response.next_question = question_payload(selected)
        return response

    if choice == "review_lesson":
        next_level = pending_review["next_level"]
        adaptive_message = pending_review.get("adaptive_message") or None
        content = get_lesson_content(db, lesson.id, next_level)
        if not content:
            raise HTTPException(status_code=404, detail="Lesson content not found for level")

        progress.current_level = next_level
        progress.status = "learning"
        clear_pending_review(progress)
        reset_retry_choice_count(progress)

        state = get_or_create_user_state(db, progress.user_id)
        sync_user_state_from_lesson(state, lesson, next_level)
        db.commit()

        response = base_submit_response(progress)
        response.lesson_content_update = build_lesson_content_update(progress, lesson.id, content, adaptive_message)
        return response

    raise HTTPException(status_code=400, detail="Unknown retry decision")


def apply_decision(
    db: Session,
    user_id: int,
    lesson: Lesson,
    progress: UserLessonProgress,
    score: int,
    total: int,
    question_ids: list[int],
) -> SubmitResponse:
    percentage = round((score / total) * 100) if total else 0
    current_level = progress.current_level
    next_lesson = get_next_lesson(db, lesson)
    next_lesson_id = next_lesson.id if next_lesson else None
    mastered = False
    needs_hints = current_level == "eli10" and score < total
    passed = percentage == PASS_PERCENTAGE
    counts = answer_counts(progress)
    retry_choice_count = get_retry_choice_count(progress)

    can_retry = False
    retry_prompt = None
    if passed:
        interpretation = "pass"
        correct_count = counts["correct"] + 1
        wrong_count = counts["wrong"]
        clear_pending_review(progress)
        reset_retry_choice_count(progress)
        if correct_count >= ANSWER_THRESHOLD:
            promoted_level = level_after_pass(current_level)
            reset_answer_counts(progress)
            if current_level == DEFAULT_LEVEL:
                status = "completed"
                mastered = True
                progress.mastery_status = "mastered"
                next_level = DEFAULT_LEVEL
                progress.quiz_completed = True
                feedback = "Continue to the next lesson."
            else:
                status = "learning"
                progress.mastery_status = "learning"
                next_level = promoted_level
                progress.quiz_completed = False
                feedback = "Great progress. Move up to the next level for this lesson."
        else:
            status = "quiz_active"
            next_level = current_level
            progress.mastery_status = "learning"
            save_answer_counts(progress, correct_count, wrong_count)
            can_retry = True
            progress.quiz_completed = False
            feedback = "Continue."
    else:
        interpretation = "fail"
        for question_id in question_ids:
            remember_failed_question(progress, current_level, question_id)

        correct_count = counts["correct"]
        wrong_count = counts["wrong"] + 1
        progress.mastery_status = "learning"
        if wrong_count >= ANSWER_THRESHOLD:
            prev_level = current_level
            next_level = level_after_fail(prev_level)
            adaptive_message = get_adaptive_message(prev_level, next_level)
            if retry_choice_count < RETRY_LIMIT:
                status = "retry_choice"
                next_level = current_level
                set_pending_review(progress, level_after_fail(prev_level), adaptive_message)
                reset_answer_counts(progress)
                progress.quiz_completed = False
                feedback = "Choose how you'd like to continue."
                retry_prompt = RetryPrompt(
                    action="RETRY_CHOICE",
                    message="We can try another question, or look at this lesson in a simpler way.",
                    retry_label="Try another question",
                    review_label="Review the lesson",
                )
            else:
                status = "learning"
                clear_pending_review(progress)
                reset_retry_choice_count(progress)
                reset_answer_counts(progress)
                progress.quiz_completed = False
                feedback = "Review the lesson, then continue."
        else:
            status = "quiz_active"
            next_level = current_level
            adaptive_message = None
            save_answer_counts(progress, correct_count, wrong_count)
            can_retry = True
            progress.quiz_completed = False
            feedback = "Continue."
        if needs_hints:
            progress.hint_usage += 1

    if passed:
        adaptive_message = None

    progress.current_level = next_level
    progress.last_score = score
    progress.best_score = max(progress.best_score or 0, score)
    progress.attempts += 1
    progress.status = status
    progress.confidence = confidence_score(percentage, progress.attempts)
    progress.read_completed = True
    progress.quiz_unlocked = True

    state = get_or_create_user_state(db, user_id)
    if mastered and next_lesson:
        sync_user_state_from_lesson(state, next_lesson, DEFAULT_LEVEL)
    else:
        sync_user_state_from_lesson(state, lesson, next_level)

    db.commit()

    next_question = None
    lesson_content_update = None
    lesson_complete = mastered

    if can_retry:
        selected = get_next_question(db, lesson.id, next_level, progress)
        next_question = question_payload(selected)
    elif passed and not mastered:
        content = get_lesson_content(db, lesson.id, next_level)
        if content:
            lesson_content_update = build_lesson_content_update(progress, lesson.id, content, None)
    elif retry_prompt is None and not mastered:
        content = get_lesson_content(db, lesson.id, next_level)
        if content:
            lesson_content_update = build_lesson_content_update(progress, lesson.id, content, adaptive_message)

    return SubmitResponse(
        score=score,
        total=total,
        percentage=percentage,
        level=next_level,
        status=status,
        interpretation=interpretation,
        mastered=mastered,
        next_lesson_id=next_lesson_id,
        needs_hints=needs_hints,
        feedback=feedback,
        can_retry=can_retry,
        next_question=next_question,
        lesson_complete=lesson_complete,
        lesson_content_update=lesson_content_update,
        retry_prompt=retry_prompt,
    )


def lesson_payload(db: Session, user_id: int, lesson_id: int) -> LessonResponse:
    lesson = get_lesson_model(db, lesson_id)
    progress = get_lesson_progress(db, user_id, lesson_id)
    level = resolve_level(progress)
    content = get_lesson_content(db, lesson_id, level)
    if not content:
        raise HTTPException(status_code=404, detail="Lesson content not found for level")

    state = get_or_create_user_state(db, user_id)
    sync_user_state_from_lesson(state, lesson, level)
    db.commit()

    return LessonResponse(
        lesson_id=lesson.id,
        title=lesson.title,
        course=lesson.topic.module.course.title,
        module=lesson.topic.module.title,
        topic=lesson.topic.title,
        objective=lesson.objective,
        practice_task=lesson.practice_task,
        content=content.content,
        level=level,
        attempts=progress.attempts if progress else 0,
        last_score=progress.last_score if progress else None,
        status=progress.status if progress else "learning",
        mastery_status=progress.mastery_status if progress else "not_started",
        practice_exercises=[
            PracticeExerciseItem(
                id=exercise.id,
                title=exercise.title,
                prompt=exercise.prompt,
                starter_code=exercise.starter_code,
                expected_output=exercise.expected_output,
                allowed_commands=exercise.allowed_commands or [],
                sequence=exercise.sequence,
                is_required=exercise.is_required,
            )
            for exercise in sorted(lesson.practice_exercises, key=lambda item: (item.sequence, item.id))
        ],
        labs=[
            LabItem(
                id=lab.id,
                title=lab.title,
                description=lab.description,
                sequence=lab.sequence,
                is_required=lab.is_required,
                tasks=[
                    LabTaskItem(
                        id=task.id,
                        title=task.title,
                        instruction=task.instruction,
                        starter_code=task.starter_code,
                        expected_output=task.expected_output,
                        allowed_commands=task.allowed_commands or [],
                        validation=task.validation,
                        sequence=task.sequence,
                    )
                    for task in sorted(lab.tasks, key=lambda item: (item.sequence, item.id))
                ],
            )
            for lab in sorted(lesson.labs, key=lambda item: (item.sequence, item.id))
        ],
    )


def get_ordered_lessons(db: Session) -> list[Lesson]:
    return db.execute(lesson_ordering()).scalars().all()


def get_mastered_lesson_ids(db: Session, user_id: int) -> set[int]:
    return set(
        db.execute(
            select(UserLessonProgress.lesson_id).where(
                UserLessonProgress.user_id == user_id,
                UserLessonProgress.mastery_status == "mastered",
            )
        ).scalars().all()
    )


def get_unlocked_lesson_ids(db: Session, user_id: int, lessons: list[Lesson] | None = None) -> set[int]:
    ordered_lessons = lessons if lessons is not None else get_ordered_lessons(db)
    if DEV_UNLOCK_ALL_CONTENT:
        return {lesson.id for lesson in ordered_lessons}

    mastered_lesson_ids = get_mastered_lesson_ids(db, user_id)
    unlocked_lesson_ids: set[int] = set()
    previous_lessons_mastered = True

    for lesson in ordered_lessons:
        mastered = lesson.id in mastered_lesson_ids
        if previous_lessons_mastered:
            unlocked_lesson_ids.add(lesson.id)
        previous_lessons_mastered = previous_lessons_mastered and mastered

    return unlocked_lesson_ids


def ensure_lesson_unlocked(db: Session, user_id: int, lesson_id: int) -> None:
    get_lesson_model(db, lesson_id)
    if DEV_UNLOCK_ALL_CONTENT:
        return
    if lesson_id not in get_unlocked_lesson_ids(db, user_id):
        raise HTTPException(status_code=403, detail="Lesson is locked")


def get_resume_lesson_id(db: Session, user_id: int, lesson_id: int) -> int:
    get_lesson_model(db, lesson_id)
    ordered_lessons = get_ordered_lessons(db)
    unlocked_lesson_ids = get_unlocked_lesson_ids(db, user_id, ordered_lessons)
    if lesson_id in unlocked_lesson_ids:
        return lesson_id

    mastered_lesson_ids = get_mastered_lesson_ids(db, user_id)
    fallback = next(
        (lesson for lesson in ordered_lessons if lesson.id in unlocked_lesson_ids and lesson.id not in mastered_lesson_ids),
        None,
    )
    if fallback:
        return fallback.id
    return ordered_lessons[0].id if ordered_lessons else get_first_lesson(db).id


@router.get("/courses", response_model=list[CourseHierarchyItem])
def get_course_hierarchy(db: Session = Depends(get_db)):
    courses = db.execute(
        select(Course)
        .options(
            selectinload(Course.modules)
            .selectinload(Module.topics)
            .selectinload(Topic.lessons)
            .selectinload(Lesson.contents),
            selectinload(Course.modules)
            .selectinload(Module.topics)
            .selectinload(Topic.lessons)
            .selectinload(Lesson.questions),
        )
        .order_by(Course.sequence, Course.id)
    ).scalars().all()

    payload: list[CourseHierarchyItem] = []
    for course in courses:
        modules: list[ModuleHierarchyItem] = []
        for module in sorted(course.modules, key=lambda item: (item.sequence, item.id)):
            topics: list[TopicHierarchyItem] = []
            for topic in sorted(module.topics, key=lambda item: (item.sequence, item.id)):
                lessons: list[LessonHierarchyItem] = []
                for lesson in sorted(topic.lessons, key=lambda item: (item.sequence, item.id)):
                    lessons.append(
                        LessonHierarchyItem(
                            id=lesson.id,
                            title=lesson.title,
                            slug=lesson.slug,
                            sequence=lesson.sequence,
                            lesson_type=lesson.lesson_type,
                            difficulty=lesson.difficulty,
                            contents=[
                                LessonHierarchyContent(
                                    id=content.id,
                                    level=content.level,
                                    content_type=content.content_type,
                                    title=content.title,
                                    sequence=content.sequence,
                                )
                                for content in sorted(lesson.contents, key=lambda item: (item.sequence, item.id))
                            ],
                            questions=[
                                LessonHierarchyQuestion(
                                    id=question.id,
                                    level=question.level,
                                    question_type=question.question_type,
                                    sequence=question.sequence,
                                    difficulty=question.difficulty,
                                )
                                for question in sorted(lesson.questions, key=lambda item: (item.sequence, item.id))
                            ],
                        )
                    )
                topics.append(
                    TopicHierarchyItem(
                        id=topic.id,
                        title=topic.title,
                        slug=topic.slug,
                        sequence=topic.sequence,
                        lessons=lessons,
                    )
                )
            modules.append(
                ModuleHierarchyItem(
                    id=module.id,
                    title=module.title,
                    slug=module.slug,
                    sequence=module.sequence,
                    topics=topics,
                )
            )
        payload.append(
            CourseHierarchyItem(
                id=course.id,
                title=course.title,
                slug=course.slug,
                sequence=course.sequence,
                modules=modules,
            )
        )
    return payload


@router.get("/getConcept", response_model=LessonResponse)
@router.get("/lesson", response_model=LessonResponse)
def get_current_lesson(
    user_id: int | None = Query(None),
    lesson_id: int | None = Query(None),
    sublevel_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    resolved_user_id = resolve_user_id(user_id, current_user)
    resolved_lesson_id = resolve_lesson_id(db, resolved_user_id, lesson_id, sublevel_id)
    if lesson_id is None and sublevel_id is None:
        resolved_lesson_id = get_resume_lesson_id(db, resolved_user_id, resolved_lesson_id)
    else:
        ensure_lesson_unlocked(db, resolved_user_id, resolved_lesson_id)
    return lesson_payload(db, resolved_user_id, resolved_lesson_id)


@router.get("/lessons", response_model=list[LessonListItem])
@router.get("/concepts", response_model=list[LessonListItem])
def get_lessons(
    user_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    resolved_user_id = resolve_user_id(user_id, current_user)
    lessons = get_ordered_lessons(db)

    unlocked_lesson_ids = get_unlocked_lesson_ids(db, resolved_user_id, lessons)
    items = []
    for lesson in lessons:
        progress = get_lesson_progress(db, resolved_user_id, lesson.id)
        items.append(
            LessonListItem(
                lesson_id=lesson.id,
                title=lesson.title,
                course=lesson.topic.module.course.title,
                module=lesson.topic.module.title,
                topic=lesson.topic.title,
                sequence=lesson.sequence,
                attempts=progress.attempts if progress else 0,
                status=progress.status if progress else "learning",
                mastery_status=progress.mastery_status if progress else "not_started",
                locked=lesson.id not in unlocked_lesson_ids,
                labs=[
                    LabItem(
                        id=lab.id,
                        title=lab.title,
                        description=lab.description,
                        sequence=lab.sequence,
                        is_required=lab.is_required,
                        tasks=[
                            LabTaskItem(
                                id=task.id,
                                title=task.title,
                                instruction=task.instruction,
                                starter_code=task.starter_code,
                                expected_output=task.expected_output,
                                allowed_commands=task.allowed_commands or [],
                                validation=task.validation,
                                sequence=task.sequence,
                            )
                            for task in sorted(lab.tasks, key=lambda item: (item.sequence, item.id))
                        ],
                    )
                    for lab in sorted(lesson.labs, key=lambda item: (item.sequence, item.id))
                ],
            )
        )
    return items


@router.get("/lesson/{lesson_id}", response_model=LessonResponse)
def get_lesson(
    lesson_id: int,
    user_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    resolved_user_id = resolve_user_id(user_id, current_user)
    ensure_lesson_unlocked(db, resolved_user_id, lesson_id)
    return lesson_payload(db, resolved_user_id, lesson_id)


@router.get("/sublevel/{sublevel_id}", response_model=LessonResponse)
def get_sublevel_alias(
    sublevel_id: int,
    user_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    return get_lesson(lesson_id=sublevel_id, user_id=user_id, db=db, current_user=current_user)


@router.get("/quiz", response_model=QuizResponse)
def get_adaptive_quiz(
    user_id: int | None = Query(None),
    lesson_id: int | None = Query(None),
    sublevel_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    resolved_user_id = resolve_user_id(user_id, current_user)
    resolved_lesson_id = resolve_lesson_id(db, resolved_user_id, lesson_id, sublevel_id)
    ensure_lesson_unlocked(db, resolved_user_id, resolved_lesson_id)
    progress = get_lesson_progress(db, resolved_user_id, resolved_lesson_id)
    level = resolve_level(progress)
    pending_review = get_pending_review(progress) if progress else None
    if pending_review:
        return QuizResponse(
            lesson_id=resolved_lesson_id,
            level=level,
            questions=[],
            retry_prompt=RetryPrompt(
                action="RETRY_CHOICE",
                message="We can try another question, or look at this lesson in a simpler way.",
                retry_label="Try another question",
                review_label="Review the lesson",
            ),
        )

    selected = get_next_question(db, resolved_lesson_id, level, progress)
    return QuizResponse(lesson_id=resolved_lesson_id, level=level, questions=[question_payload(selected)])


@router.get("/quiz/{lesson_id}", response_model=QuizResponse)
def get_quiz(
    lesson_id: int,
    user_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    return get_adaptive_quiz(user_id=user_id, lesson_id=lesson_id, db=db, current_user=current_user)


@router.post("/submitQuiz", response_model=SubmitResponse)
def submit_adaptive_quiz(
    submit_request: SubmitRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    resolved_user_id = resolve_user_id(submit_request.user_id, current_user)
    try:
        lesson_id = submit_request.resolved_lesson_id()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    ensure_lesson_unlocked(db, resolved_user_id, lesson_id)
    lesson = get_lesson_model(db, lesson_id)
    progress = get_or_create_lesson_progress(db, resolved_user_id, lesson_id)

    if submit_request.decision:
        return resolve_retry_decision(db, lesson, progress, submit_request.decision)

    question_ids = [answer.question_id for answer in submit_request.answers]
    questions = db.execute(
        select(Question).where(
            Question.id.in_(question_ids),
            Question.lesson_id == lesson_id,
        )
    ).scalars().all()
    answer_map = {question.id: question.correct_answer for question in questions}

    score = 0
    for answer in submit_request.answers:
        if answer_map.get(answer.question_id) == answer.selected:
            score += 1

    return apply_decision(
        db=db,
        user_id=resolved_user_id,
        lesson=lesson,
        progress=progress,
        score=score,
        total=len(submit_request.answers),
        question_ids=question_ids,
    )


@router.post("/submit", response_model=SubmitResponse)
def submit_quiz(
    submit_request: SubmitRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    return submit_adaptive_quiz(submit_request=submit_request, db=db, current_user=current_user)


@router.get("/nextStep", response_model=NextResponse)
def get_next_step(
    user_id: int | None = Query(None),
    lesson_id: int | None = Query(None),
    sublevel_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    resolved_user_id = resolve_user_id(user_id, current_user)
    resolved_lesson_id = resolve_lesson_id(db, resolved_user_id, lesson_id, sublevel_id)
    lesson = get_lesson_model(db, resolved_lesson_id)
    progress = get_lesson_progress(db, resolved_user_id, resolved_lesson_id)

    if not progress or progress.status == "learning":
        content = get_lesson_content(db, resolved_lesson_id, DEFAULT_LEVEL)
        return NextResponse(
            completed=False,
            lesson_id=resolved_lesson_id,
            level=DEFAULT_LEVEL,
            content=content.content if content else None,
            message="Start with the first lesson content.",
        )

    if progress.status == "completed" and progress.mastery_status == "mastered":
        next_lesson = get_next_lesson(db, lesson)
        if next_lesson:
            content = get_lesson_content(db, next_lesson.id, DEFAULT_LEVEL)
            return NextResponse(
                completed=True,
                lesson_id=next_lesson.id,
                level=DEFAULT_LEVEL,
                content=content.content if content else None,
                message=f"Continue with {next_lesson.title}.",
                next_lesson_id=next_lesson.id,
            )
        return NextResponse(
            completed=True,
            lesson_id=lesson.id,
            level=progress.current_level,
            content=None,
            message="Course complete.",
        )

    content = get_lesson_content(db, resolved_lesson_id, progress.current_level)
    if not content:
        raise HTTPException(status_code=404, detail="Next lesson content not found")

    if progress.status == "quiz_active":
        message = "Continue when you are ready."
    elif progress.status == "learning":
        message = "Review the lesson, then continue."
    else:
        message = "Continue when you are ready."

    return NextResponse(
        completed=False,
        lesson_id=resolved_lesson_id,
        level=progress.current_level,
        content=content.content,
        message=message,
    )


@router.get("/next/{lesson_id}", response_model=NextResponse)
def get_next(
    lesson_id: int,
    user_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    return get_next_step(user_id=user_id, lesson_id=lesson_id, db=db, current_user=current_user)
