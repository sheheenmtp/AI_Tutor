# Architecture Overview

This repository is organized as a monorepo containing two application modules and shared infrastructure:

- `pytutor/` — coding-practice tutoring application (Judge0 + Ollama + PostgreSQL)
- `course_tutor/` — course-based adaptive learning platform (Linux course included)
- `shared/` — shared utilities, schemas, and database helpers (place for truly shared code)

Each application contains its own `frontend/` and `backend/` where applicable. Backends use FastAPI and SQLAlchemy; frontends use Vite/React.

Design goals:
- Keep applications logically independent.
- Preserve existing APIs, database schemas, and environment variables.
- Make it easy to add additional courses under `course_tutor/courses/`.
