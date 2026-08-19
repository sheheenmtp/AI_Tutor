# PyTutor

This folder is the canonical home for the PyTutor application (coding practice).

Current implementation is in the legacy folder `pytutor/legacy_py_tutor/` — the code and configuration remain there for now.

Planned structure:

- `pytutor/backend/` — FastAPI backend (models, api, services)
- `pytutor/frontend/` — React/Vite frontend
- `pytutor/Dockerfile` and `pytutor/docker-compose.yml`

We intentionally keep the original code under `pytutor/legacy_py_tutor/` during migration. Follow `docs/setup.md` to run the PyTutor app.
