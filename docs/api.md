# API Notes

Backends expose FastAPI applications. Key endpoints:

- PyTutor backend (`/pytutor/backend`): user management, code run/submit, feedback (`/auth`, `/run`, `/submit`, `/feedback`), health checks.
- Course Tutor backend (`/course_tutor/backend`): course navigation, runner (`/runner/bash`), teacher chat (`/chat/teacher/stream`) and lesson APIs.

Environment variables such as `DATABASE_URL`, `JUDGE0_URL`, and `OLLAMA_URL` are required.
