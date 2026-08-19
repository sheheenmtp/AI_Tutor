from typing import List, Optional

from pydantic import BaseModel, Field


class PracticeExerciseItem(BaseModel):
    id: int
    title: str
    prompt: str
    starter_code: str
    expected_output: Optional[str]
    allowed_commands: List[str]
    sequence: int
    is_required: bool


class LabTaskItem(BaseModel):
    id: int
    title: str
    instruction: str
    starter_code: str
    expected_output: Optional[str]
    allowed_commands: List[str]
    validation: Optional[dict] = None
    sequence: int


class LabItem(BaseModel):
    id: int
    title: str
    description: str
    sequence: int
    is_required: bool
    tasks: List[LabTaskItem]


class LessonResponse(BaseModel):
    lesson_id: int
    title: str
    course: str
    module: str
    topic: str
    objective: Optional[str] = None
    practice_task: Optional[str] = None
    content: str
    level: str
    attempts: int
    last_score: Optional[int]
    status: str
    mastery_status: str
    practice_exercises: List[PracticeExerciseItem] = []
    labs: List[LabItem] = []


class BashRunRequest(BaseModel):
    exercise_id: Optional[int] = None
    lab_task_id: Optional[int] = None
    source_code: str
    stdin: str = ""


class ChatHistoryMessage(BaseModel):
    role: str
    content: str


class TeacherChatRequest(BaseModel):
    lesson_id: int
    message: str
    level: Optional[str] = "standard"
    view: Optional[str] = "lesson"
    lab_id: Optional[int] = None
    lab_title: Optional[str] = None
    history: List[ChatHistoryMessage] = Field(default_factory=list)


class TeacherChatResponse(BaseModel):
    reply: str
    model: str


class LessonListItem(BaseModel):
    lesson_id: int
    title: str
    course: str
    module: str
    topic: str
    sequence: int
    attempts: int
    status: str
    mastery_status: str
    locked: bool
    labs: List[LabItem] = []


class QuizQuestion(BaseModel):
    question_id: int
    question: str
    options: List[str]
    question_type: str


class RetryPrompt(BaseModel):
    action: str
    message: str
    retry_label: str
    review_label: str


class QuizResponse(BaseModel):
    lesson_id: int
    level: str
    questions: List[QuizQuestion]
    retry_prompt: Optional[RetryPrompt] = None


class LessonContentUpdate(BaseModel):
    lesson_id: int
    action: str
    content: str
    adaptive_message: Optional[str] = None


class AnswerPayload(BaseModel):
    question_id: int
    selected: str


class SubmitRequest(BaseModel):
    user_id: Optional[int] = None
    lesson_id: Optional[int] = None
    sublevel_id: Optional[int] = None
    answers: List[AnswerPayload]
    decision: Optional[str] = None

    def resolved_lesson_id(self) -> int:
        lesson_id = self.lesson_id or self.sublevel_id
        if lesson_id is None:
            raise ValueError("lesson_id is required")
        return lesson_id


class SubmitResponse(BaseModel):
    score: int
    total: int
    percentage: int
    level: str
    status: str
    interpretation: str
    mastered: bool
    next_lesson_id: Optional[int]
    needs_hints: bool
    feedback: str
    can_retry: bool
    next_question: Optional[QuizQuestion] = None
    lesson_complete: bool = False
    lesson_content_update: Optional[LessonContentUpdate] = None
    retry_prompt: Optional[RetryPrompt] = None


class NextResponse(BaseModel):
    completed: bool
    lesson_id: Optional[int]
    level: Optional[str]
    content: Optional[str]
    message: str
    next_lesson_id: Optional[int] = None


class LessonHierarchyContent(BaseModel):
    id: int
    level: str
    content_type: str
    title: Optional[str]
    sequence: int


class LessonHierarchyQuestion(BaseModel):
    id: int
    level: str
    question_type: str
    sequence: int
    difficulty: Optional[str]


class LessonHierarchyItem(BaseModel):
    id: int
    title: str
    slug: str
    sequence: int
    lesson_type: str
    difficulty: str
    contents: List[LessonHierarchyContent]
    questions: List[LessonHierarchyQuestion]


class TopicHierarchyItem(BaseModel):
    id: int
    title: str
    slug: str
    sequence: int
    lessons: List[LessonHierarchyItem]


class ModuleHierarchyItem(BaseModel):
    id: int
    title: str
    slug: str
    sequence: int
    topics: List[TopicHierarchyItem]


class CourseHierarchyItem(BaseModel):
    id: int
    title: str
    slug: str
    sequence: int
    modules: List[ModuleHierarchyItem]


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username_or_email: str
    password: str


class AuthUser(BaseModel):
    id: int
    username: str
    email: str


class AuthResponse(BaseModel):
    token: str
    user: AuthUser
