# AI_Tutor

AI_Tutor is a monorepo containing two learning applications:

- `pytutor/` — coding practice platform (Judge0 execution + Ollama hints)
- `course_tutor/` — adaptive course platform (Linux course provided)

Repository highlights:

- Backends: FastAPI + SQLAlchemy (PostgreSQL)
- Frontends: Vite + React
- LLM: Ollama-compatible endpoints supported
- Code execution: Judge0 integration

See `docs/` for architecture and setup instructions.

To get started locally:

1. Copy `.env.example` to `.env` and set values.
2. Start the database (Postgres) and optional services:

```bash
# Example using Docker Compose if provided per-application
docker compose -f course_tutor/docker-compose.yml up -d
docker compose -f pytutor/legacy_py_tutor/docker-compose.yml up -d
```

3. Start backends and frontends as documented in `docs/setup.md`.
# AI Tutor

A full-stack coding practice platform for learners to solve problems, validate code, track progress, and receive AI-guided hints.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com)

## Overview
AI Tutor is a coding practice and adaptive learning application designed to help a learner improve through guided problem solving. The platform combines a browser-based editor, persistent user progress, code execution, and AI-powered feedback to support a more effective learning flow.

Users can:
- register and log in
- browse a curated set of coding challenges
- receive recommendations based on progress and concept mastery
- write and edit code in a Monaco-based editor
- validate solutions against sample and hidden tests
- submit work and track scores
- request level-aware AI hints and explanations

## Key Features
- User authentication and profile tracking
- Adaptive recommendation engine for challenge sequencing
- Problem bank with difficulty and concept organization
- Browser-based coding environment
- Validation and scoring through Judge0
- Submission history and progress persistence in PostgreSQL
- AI feedback generation from Ollama
- Responsive frontend experience built with React and Vite

## Architecture
The project uses a simple three-layer architecture:

1. Frontend
   - React + Vite single-page app
   - Renders the coding workspace, question bank, and profile panels
   - Calls the API for auth, problem data, validation, and AI feedback

2. Backend
   - FastAPI application in backend/app.py
   - SQLAlchemy models and DB setup in backend/models.py
   - Serves endpoints for registration, login, recommendations, problem access, validation, submissions, and streaming feedback

3. External services
   - PostgreSQL stores users, concepts, problems, submissions, and mastery state
   - Judge0 executes submitted code and checks expected output
   - Ollama provides AI-generated hints and explanations

## Technology Stack
- Python 3.10+
- FastAPI
- SQLAlchemy
- Pydantic
- PostgreSQL
- React
- Vite
- Monaco Editor
- Docker Compose
- Judge0
- Ollama
- Python requests and python-dotenv

## Project Structure
```text
AI_Tutor/
├── backend/
│   ├── app.py               # FastAPI routes and logic
│   ├── models.py            # SQLAlchemy models and DB session setup
│   ├── requirements.txt     # Python dependencies
│   ├── seed_data.py         # Seed problem and concept data
│   ├── .env.example         # Sample backend env file
│   └── .venv/               # Local Python environment (ignored by Git)
├── frontend/
│   ├── src/                 # React application source
│   ├── public/              # Static assets
│   ├── package.json         # Frontend dependencies and scripts
│   ├── .env.example         # Sample frontend env file
│   ├── vite.config.js       # Vite config
│   ├── package-lock.json    # Frontend lockfile
│   └── .gitignore           # Frontend-specific ignores
├── docker-compose.yml       # PostgreSQL service definition
├── Makefile                 # Local setup and automation shortcuts
├── run.sh                   # Starts backend + frontend together
├── README.md                # Project overview and setup guide
├── LICENSE                  # Project license
├── .gitignore               # Runtime and secret exclusions
├── .env.example             # Shared environment placeholders
├── database.json            # Local/reference dataset
├── codemastery_full.sql     # Full SQL dump/export
├── codemastery_schema.sql   # Schema export
├── problem_concept_backfill.sql
├── user_auth_migration.sql
├── PROJECT_INFO.md          # Project metadata notes
├── KNOWLEDGE_TRANSFER.md    # Design and handoff notes
├── PROJECT_WORKING.md       # Implementation detail notes
├── ADAPTIVE_SYSTEM_DEEP_DIVE.md
├── .gitlab-ci.yml          # GitLab CI config retained for reference
└── .gitignore
```

## Repository Modules

This monorepo contains two separately runnable applications. They are organized so you can work on, start, and verify each app independently.

- **`course_tutor/` — Adaptive course platform**
   - Path: `course_tutor/`
   - Backend: FastAPI entry `course_tutor/backend/main.py` (uses JSONB fields — PostgreSQL required). Default port: `8000`.
   - Frontend: Vite app in `course_tutor/frontend/`. Default dev port: `5174`.
   - DB: create a Postgres database named `course_tutor` (or point `DATABASE_URL` to your DB). Use `course_tutor/backend/seed.py` to seed content after the backend has created tables.
   - Start (example):

   ```bash
   # backend
   cd course_tutor/backend
   source .venv/bin/activate  # if using the included venv
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload

   # frontend
   cd ../frontend
   npm run dev -- --host
   ```

- **`pytutor/` — Coding-practice platform (legacy PyTutor moved)**
   - Path: `pytutor/legacy_py_tutor/` contains the original PyTutor application (backend + frontend + dumps).
   - Shims: `pytutor/backend/app.py` and `pytutor/__init__.py` let you run the app via the `pytutor` package (the shim imports from the legacy folder). Default shim backend port: `8001` in our local setup.
   - Frontend: legacy frontend at `pytutor/legacy_py_tutor/frontend/`. Default dev port: `5175`. If the frontend points to the wrong backend, update `VITE_API_URL` in that folder's `.env`.
   - Seed: run `pytutor/legacy_py_tutor/backend/seed_data.py` after the PyTutor backend has created tables.
   - Start (example):

   ```bash
   # shim backend (delegates to legacy app)
   uvicorn pytutor.backend.app:app --host 0.0.0.0 --port 8001 --reload

   # legacy frontend
   cd pytutor/legacy_py_tutor/frontend
   npm run dev -- --host
   ```

Verification (quick smoke checks)
- Course Tutor health: `curl http://localhost:8000/health`
- PyTutor health: `curl http://localhost:8001/health`
- Register a quick user on each backend:

```bash
curl -X POST http://localhost:8000/auth/register -H 'Content-Type: application/json' -d '{"email":"test@example.com","password":"pass"}'
curl -X POST http://localhost:8001/auth/register -H 'Content-Type: application/json' -d '{"email":"test2@example.com","password":"pass"}'
```

Notes and gotchas
- `course_tutor` requires PostgreSQL (JSONB) — do not run it on SQLite.
- We intentionally moved the original `py_tutor/` into `pytutor/legacy_py_tutor/` and added lightweight shims in `pytutor/` so imports and run commands continue to work during the migration.
- Do not commit real secrets — only `.env.example` files are tracked. Large SQL dumps are included in the legacy folder; confirm company policy before pushing them to a remote.

## Installation
### Prerequisites
- Python 3.10 or newer
- Node.js 20 or newer
- Docker and Docker Compose
- Git

### 1) Clone the repository
```bash
git clone https://github.com/sheheenmtp/AI_Tutor.git
cd AI_Tutor
```

### 2) Create environment files
```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 3) Install dependencies
```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
npm ci --prefix frontend
```

### 4) Start the database
```bash
docker compose up -d postgres
```

### 5) Seed the application data
```bash
cd backend
source .venv/bin/activate
python seed_data.py
```

## Environment Variables
This project uses environment variables for local service configuration.

Example root file:
```env
DATABASE_URL=postgresql+psycopg2://<username>:<password>@<host>:5432/<database_name>
JUDGE0_URL=http://localhost:2358
OLLAMA_URL=http://localhost:11434
VITE_API_URL=http://localhost:8000
```

Use placeholder values only. Never commit real credentials or local `.env` files.

## Running the Application
### Backend
```bash
cd backend
source .venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend
```bash
cd frontend
npm run dev -- --host
```

### Database
```bash
docker compose up -d postgres
```

### Required AI services
Judge0 and Ollama should be reachable locally before validation or feedback calls:
- http://localhost:2358
- http://localhost:11434

## AI/LLM Setup
This app expects Ollama to be running with the model `qwen2.5-coder:14b` available.

```bash
ollama pull qwen2.5-coder:14b
```

The backend calls Ollama at `/api/generate` and expects either streaming or non-streaming responses for hint generation.

## API
The backend exposes REST endpoints for its main workflows.

Key routes:
- `GET /health` — checks backend, Judge0, and Ollama status
- `POST /auth/register` — create a new user
- `POST /auth/login` — authenticate a user
- `GET /problems` — fetch the problem list
- `GET /problems/{problem_id}` — fetch a specific problem and sample tests
- `POST /validate` — validate code without saving a submission
- `POST /submit` — run tests, save a submission, and update progress
- `POST /feedback` — generate a single AI feedback response
- `POST /feedback/stream` — stream AI feedback chunks to the frontend
- `GET /languages` — list Judge0-supported languages

## Development
For local development:

```bash
make setup
make db-up
cd backend && source .venv/bin/activate && python seed_data.py
make dev
```

The application is designed to run locally with PostgreSQL and the external Judge0/Ollama services online. If these services are offline, the app will still start, but execution and AI hint generation will not work until they are available.

## Testing
This repository does not currently include a dedicated automated test suite. The practical validation used in this project is:

```bash
python3 -m compileall -q backend
npm run build --prefix frontend
```

## Limitations
- There is no production-grade deployment setup for cloud hosting.
- The app depends on local Judge0 and Ollama services.
- The Ollama model is hardcoded in the backend and should be kept in sync with the local installation.
- The repository does not yet include an automated GitHub Actions workflow.
- The database is configured for local development rather than a managed production environment.

## Future Improvements
- Add automated backend and frontend tests
- Add GitHub Actions checks for linting and build validation
- Support configurable Ollama model selection through environment variables
- Improve production deployment configuration
- Expand the problem bank and learner analytics

## Developer
**Muhammed Sheheen M T P**

## Original Repository
https://github.com/sheheenmtp/AI_Tutor

This repository is intended for public GitHub presentation while preserving the original developer attribution and implementation history.
