# Local Setup

1. Copy `.env.example` to `.env` and set values for `DATABASE_URL`, `JUDGE0_URL`, and `OLLAMA_URL`.

2. To run PyTutor backend:

```bash
cd pytutor/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8001
```

3. To run Course Tutor backend:

```bash
cd course_tutor/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

4. Frontends:

Each frontend has its own `package.json`. From the relevant frontend directory run `npm install` and `npm run dev`.

5. Docker:

Docker support is preserved per-application. See `pytutor/docker-compose.yml` or `course_tutor/docker-compose.yml` where present.
