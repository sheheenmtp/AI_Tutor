# Knowledge Transfer: Linux Adaptive Tutor

## Project Summary

Linux Adaptive Tutor is a full-stack adaptive learning prototype for a Linux userspace course. It combines:

- A FastAPI backend with PostgreSQL persistence.
- A React/Vite frontend styled with Tailwind and custom CSS.
- Generated lesson JSON under `Data/generated/`.
- Adaptive quiz behavior that moves learners between `standard`, `layman`, and `eli10` explanation levels.
- Optional Bash practice/lab execution through Judge0.
- Teacher chat through an Ollama-compatible local model endpoint.

The current course/module/topic/lesson model is active. Direct SQL compatibility for migrating older `topic/sublevel` databases remains in `backend/migration.py`; see **Current Handover Risks** before changing schema code.

## Repository Map

| Path | Purpose |
| --- | --- |
| `backend/main.py` | FastAPI app entry point. Registers routers, CORS, startup migration, table creation, and seed loading. |
| `backend/db.py` | SQLAlchemy engine/session setup. Requires `DATABASE_URL` and loads the root `.env`. |
| `backend/models.py` | SQLAlchemy models for courses, modules, topics, lessons, content, exercises, labs, users, sessions, and progress. |
| `backend/migration.py` | SQL DDL/data migration helpers for newer course/module/topic/lesson tables. |
| `backend/seed.py` | Legacy seed path for `Data/topic1.json`; also contains starter practice/lab fixtures. |
| `backend/content_importer.py` | Validates and imports generated lesson JSON from `Data/generated/`. |
| `backend/routes/concepts.py` | Lesson listing, lesson retrieval, quiz, adaptive scoring, and progression routes. |
| `backend/routes/auth.py` | Register/login/session-token authentication. |
| `backend/routes/runner.py` | Bash runner endpoint backed by Judge0. Applies command allowlist and blocked-pattern checks. |
| `backend/routes/chat.py` | Teacher chat endpoint backed by Ollama. Supports normal and streaming responses. |
| `frontend/src/App.jsx` | Main React state machine for auth, course/lesson loading, quiz flow, lab flow, theme, and API calls. |
| `frontend/src/pages/` | Learning, quiz, and lab UI screens. |
| `frontend/src/components/TeacherChat.jsx` | Floating teacher chat UI. |
| `Data/generated/M1T1_1.json` | Example generated lesson payload. |
| `ops/migrations/legacy/linux_course_pre_lesson_migration.sql` | Sanitized SQL snapshot/migration support artifact. |
| `backend/rollback_lesson_migration.md` | Rollback notes for the lesson migration. |
| `run-backend.sh` | Convenience script to start the backend on port `8000`. |

## Runtime Architecture

1. User opens the React frontend.
2. Frontend authenticates through `/auth/register` or `/auth/login` and stores the bearer token in local storage.
3. Frontend loads course hierarchy from `/courses`, lesson list from `/concepts`, and current lesson content from `/lesson`.
4. Learner reads lesson content. Markdown is rendered with `marked` in `LearningPage.jsx`.
5. Learner starts quiz through `/quiz`.
6. Quiz submissions go to `/submitQuiz`.
7. Backend tracks progress in `user_lesson_progress`, adjusts the current explanation level, and returns either the next question, updated lesson content, a retry choice, or next-lesson information.
8. Practice/lab Bash code goes to `/runner/bash`, which validates allowed commands and sends code to Judge0.
9. Teacher chat goes to `/chat/teacher/stream`, which builds a lesson-aware prompt and streams the Ollama response.

## Setup

Backend:

```bash
cp .env.example .env
python3 -m pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Or:

```bash
./run-backend.sh
```

Frontend:

```bash
cd frontend
cp .env.example .env.local
npm ci
npm run dev
```

The frontend defaults API calls to `http://<frontend-hostname>:8000`. Override with:

```bash
VITE_API_URL=http://localhost:8000 npm run dev
```

## Environment Variables

| Variable | Requirement | Used By | Notes |
| --- | --- | --- | --- |
| `DATABASE_URL` | Required | `backend/db.py` | PostgreSQL connection string. |
| `DEV_UNLOCK_ALL_CONTENT` | `true` | `backend/routes/concepts.py` | When true, all lessons are unlocked regardless of mastery. |
| `JUDGE0_URL` | Optional integration | `backend/routes/runner.py` | Judge0 API base URL; runner returns 503 when omitted. |
| `JUDGE0_BASH_LANGUAGE_ID` | `46` | `backend/routes/runner.py` | Judge0 language ID for Bash. |
| `OLLAMA_URL` | Optional integration | `backend/routes/chat.py` | Ollama API base URL; chat returns 503 when omitted. |
| `OLLAMA_MODEL` | `qwen2.5-coder:14b` | `backend/routes/chat.py` | Teacher chat model. |

Copy `.env.example` and `frontend/.env.example`; do not commit populated environment files.

## Backend Route Surface

Authentication:

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

Course and lesson flow:

- `GET /courses`
- `GET /concepts` and `GET /lessons`
- `GET /lesson`
- `GET /lesson/{lesson_id}`
- `GET /getConcept`
- `GET /sublevel/{sublevel_id}` as compatibility alias
- `GET /quiz`
- `GET /quiz/{lesson_id}`
- `POST /submitQuiz`
- `POST /submit`
- `GET /nextStep`

Interactive services:

- `POST /runner/bash`
- `POST /chat/teacher`
- `POST /chat/teacher/stream`

Most frontend requests include `Authorization: Bearer <session_token>`.

## Adaptive Learning Logic

The intended lesson levels are:

- `standard`: default explanation.
- `layman`: simpler explanation.
- `eli10`: most simplified explanation.

Key constants in `backend/routes/concepts.py`:

- `PASS_PERCENTAGE = 100`
- `ANSWER_THRESHOLD = 3`
- `RETRY_LIMIT = 3`

Behavior summary:

- A correct answer increments the learner's correct counter for the current level.
- After enough correct answers, the learner either moves up to a harder explanation level or completes the lesson if already at `standard`.
- A wrong answer increments the wrong counter.
- After enough wrong answers, the learner can retry questions or review a simpler explanation level.
- Failed question IDs are remembered so retries can prefer unseen questions.

## Data and Content Flow

There are two content paths in this checkout:

- Legacy seed path: `backend/seed.py` expects `Data/topic1.json`.
- Generated lesson import path: `backend/content_importer.py` expects files in `Data/generated/`.

The generated importer is the more current path. It validates:

- `topic_slug`
- Optional `module_slug`
- `lesson.title`, `lesson.slug`, `lesson.sequence`, metadata, tags, examples, and common confusions
- Exactly three levels: `standard`, `layman`, `eli10`
- Exactly ten MCQ questions per level
- Four options per question
- Answer must exactly match one option
- Optional practice exercise
- Optional lab with one or more tasks
- Safe command allowlists for practice/lab tasks

Validate generated content without writing:

```bash
python -m backend.content_importer --dry-run Data/generated
```

Import generated content:

```bash
python -m backend.content_importer Data/generated
```

## Frontend State Flow

`frontend/src/App.jsx` owns most application state:

- Auth state and local storage.
- Selected course state.
- Lesson list and current lesson.
- Quiz overlay state.
- Active lab state.
- Adaptive message state.
- Theme state.

Important local storage keys:

- `linux-course-auth`
- `linux-course-selected-course`
- `linux-course-theme`

The visible screens are:

- Auth form and course selection/home in `App.jsx`.
- Lesson reading and practice in `LearningPage.jsx`.
- Quiz overlay in `QuizPage.jsx`.
- Lab workspace in `LabPage.jsx`.
- Floating teacher chat in `TeacherChat.jsx`.

## Bash Runner Notes

`POST /runner/bash` requires authentication and exactly one of:

- `exercise_id`
- `lab_task_id`

The runner rejects empty code, very long code, blocked patterns, and commands outside the target's `allowed_commands`.

Blocked examples include command substitution, `rm`, `mkfs`, `dd`, network tools, privilege tools, ownership/permission changes, and fork-bomb syntax.

Judge0 decides execution status. The backend marks `passed` true when:

- `expected_output` is configured and appears in `stdout`, or
- no expected output is configured and Judge0 returns accepted status.

## Teacher Chat Notes

The teacher chat prompt is lesson-aware. It injects:

- Course title
- Module title
- Topic title
- Lesson title
- Current view
- Lab title if present
- Current lesson content for the selected level
- Up to the last eight chat messages

The system prompt asks the model to teach Linux clearly, avoid revealing quiz answers before submission, avoid destructive commands, and redirect out-of-course questions.

## Current Handover Risks

1. The database migration is SQL-driven and not backed by Alembic.
   - `backend/migration.py` mutates schema directly on startup.
   - Keep database backups before changing schema logic.
   - A restore test of the sanitized legacy snapshot currently reaches `NoSuchTableError: lab_tasks` during startup; resolve and retest that path before a production legacy upgrade.

2. The legacy seed compatibility path remains in `backend/seed.py`.
   - It reads `Data/topic1.json` only when that optional legacy file exists.
   - `Data/generated/` and `backend/content_importer.py` are the current content workflow.

3. Judge0 and Ollama are optional but externally operated.
   - Configure their base URLs through environment variables in each target environment.

4. `DEV_UNLOCK_ALL_CONTENT` defaults to `true` for development.
   - Review this setting before validating progression behavior or deploying.

5. There is no visible test suite in this checkout.
   - Add smoke tests for backend import/startup, auth, lesson retrieval, quiz submit, content import dry-run, runner validation, and chat prompt construction.

6. `Data/generated/M1T1_1.json` currently fails JSON parsing at line 40, column 1076.
   - Correct the course-content source before expecting the generated-content dry run to pass.

## Suggested First Maintenance Steps

1. Copy `.env.example`, configure PostgreSQL, and review optional integration settings.
2. Run a backend import smoke check:

```bash
python -c "import backend.main; print('backend import ok')"
```

3. Validate content:

```bash
python -m backend.content_importer --dry-run Data/generated
```

4. Start PostgreSQL. Configure Judge0 and Ollama only when exercising runner/chat routes.
5. Run backend and frontend locally.
6. Register a test user and walk through lesson, quiz, practice, lab, and teacher chat flows.

## Ownership Checklist

For a smooth handover, the receiving engineer should know:

- How to run backend and frontend.
- How to create a user and authenticate.
- How the adaptive quiz state changes after correct/wrong answers.
- How to author and validate generated lesson JSON.
- How Judge0 and Ollama are deployed in the target environment.
- Which database instance contains the canonical course content.
- Whether `DEV_UNLOCK_ALL_CONTENT` should remain enabled in the target environment.
- How to restore the DB from backup before running migration changes.
