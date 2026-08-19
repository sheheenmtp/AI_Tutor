# Course Tutor

This application supports course-based adaptive learning. The existing Linux course lives under `course_tutor/Data` and `course_tutor/backend`.

Planned structure under `course_tutor/`:

- `backend/` — FastAPI application (`main.py`, `routes/`, `models.py`)
- `frontend/` — React frontend
- `courses/` — course content directory (e.g., `courses/linux/`)

See `docs/` for migration and setup details.
# Linux Adaptive Tutor

Linux Adaptive Tutor is a full-stack learning application for guided Linux coursework. It combines structured lessons, adaptive quizzes, safe Bash exercises, guided labs, and a lesson-aware teacher chat.

The backend is FastAPI with PostgreSQL and SQLAlchemy. The frontend is React, Vite, Tailwind CSS, and custom CSS.

## Project status

The course/module/topic/lesson schema is the primary application model. `backend/migration.py` still contains direct SQL migration support for databases created with the earlier topic/sublevel schema; Alembic is not used yet.

`Data/generated/` and `backend/content_importer.py` are the current content-authoring path. `backend/seed.py` retains optional compatibility with the legacy `Data/topic1.json` format, but that file is not required or included in a fresh checkout.

The legacy SQL snapshot under `ops/migrations/legacy/` is sanitized and retained only for migration/rollback support. It contains no user accounts, authentication material, or learner progress.

## Features

- Account registration and session-token authentication
- Course, module, topic, and lesson navigation
- Three explanation levels: `standard`, `layman`, and `eli10`
- Adaptive MCQ progression and lesson mastery tracking
- Optional Bash practice and guided labs through Judge0
- Optional streaming teacher chat through Ollama
- Light and dark frontend themes

## Repository layout

```text
backend/                  FastAPI app, SQLAlchemy models, migration, and routes
Data/generated/           Versioned generated lesson content
docs/                     Content-authoring and handover documentation
frontend/                 React/Vite application
ops/migrations/legacy/    Sanitized pre-lesson-schema rollback snapshot
.env.example              Backend and operations environment template
```

## Prerequisites

- Python 3.10 or newer
- PostgreSQL 14 or newer
- Node.js 20 or newer and npm
- Optional: a Judge0 instance for `/runner/bash`
- Optional: an Ollama-compatible server for teacher chat

## Backend setup

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
cp .env.example .env
```

Edit `.env` and set `DATABASE_URL` to a PostgreSQL database owned by your application user. The backend reads the root `.env` automatically. It stops with a clear configuration error if `DATABASE_URL` is missing.

For an empty database, startup creates the current tables. Then start the API:

```bash
./run-backend.sh
```

Alternatively:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API is available at `http://localhost:8000`; interactive documentation is at `http://localhost:8000/docs`.

## Frontend setup

In another terminal:

```bash
cd frontend
npm ci
cp .env.example .env.local
npm run dev
```

Set `VITE_API_URL` in `frontend/.env.local` when the backend is not available at the example URL. Open the URL printed by Vite, normally `http://localhost:5173`.

Build the production frontend with:

```bash
cd frontend
npm run build
```

## Environment configuration

Copy the checked-in templates and replace their placeholder values:

- Root template: `.env.example`
- Frontend template: `frontend/.env.example`

| Variable | Required | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | Yes | SQLAlchemy PostgreSQL connection URL. |
| `DATABASE_ADMIN_URL` | Operations only | Administrative PostgreSQL URL used by the documented full rollback procedure. |
| `DEV_UNLOCK_ALL_CONTENT` | No | Development override for lesson prerequisites; review before deployment. |
| `JUDGE0_URL` | For Bash execution | Judge0 base URL. The runner returns HTTP 503 when it is not configured. |
| `JUDGE0_BASH_LANGUAGE_ID` | No | Judge0 language identifier for Bash. |
| `OLLAMA_URL` | For teacher chat | Ollama base URL. Chat returns HTTP 503 when it is not configured. |
| `OLLAMA_MODEL` | No | Ollama model used by teacher chat. |
| `VITE_API_URL` | No | Backend API base URL embedded by Vite. |

Do not commit `.env` or `.env.local` files.

## Content workflow

Generated course JSON belongs in `Data/generated/` and is intentionally versioned.

Known content issue: `Data/generated/M1T1_1.json` currently has invalid JSON at line 40, column 1076. Correct that authoring error before validating or importing the generated content directory.

Once a matching course/module/topic hierarchy exists in PostgreSQL, validate generated content without committing database changes:

```bash
python -m backend.content_importer --dry-run Data/generated
```

Import it with:

```bash
python -m backend.content_importer Data/generated
```

See `docs/CONTENT_AUTHORING_GUIDE.md` for the required JSON shape and validation rules.

## Primary API flow

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `GET /courses`
- `GET /concepts`
- `GET /lesson`
- `GET /quiz`
- `POST /submitQuiz`
- `POST /runner/bash`
- `POST /chat/teacher/stream`

Judge0 and Ollama are optional external services configured only through environment variables. No internal service addresses or credentials are included in the repository.

## Migration and rollback notes

`backend/migration.py` remains the schema-migration source of truth and runs during backend startup. Back up a real database before applying migration changes.

The sanitized legacy snapshot and restore notes are here:

- `ops/migrations/legacy/linux_course_pre_lesson_migration.sql`
- `backend/rollback_lesson_migration.md`

The snapshot is a rollback artifact for use with matching pre-migration application code; it is not a fresh-install content bootstrap. The current direct migration path still needs work when upgrading that legacy snapshot (`NoSuchTableError: lab_tasks` is raised during startup), so test legacy upgrades on a disposable database before relying on them.

The checked-in snapshot cannot restore removed users, sessions, or learner progress. Use a separately secured operational backup when those records must be preserved.

## Sanity checks

With `DATABASE_URL` configured:

```bash
python -c "import backend.main; print('backend import ok')"
python -m backend.content_importer --dry-run Data/generated
cd frontend && npm run build
```

Live Judge0 and Ollama services are not required for importing the backend or building the frontend.
The content-import check currently reports the known malformed `M1T1_1.json` file noted above.

## License

No open-source license has been selected yet. Add a top-level `LICENSE` before publishing if reuse rights should be granted.
