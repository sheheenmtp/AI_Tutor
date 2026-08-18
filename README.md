# AI Tutor Platform

AI Tutor is a full-stack coding practice app with:
- FastAPI backend for problems, submissions, scoring, and AI hints
- React + Monaco frontend for solving problems
- Judge0 for code execution
- Ollama for level-aware feedback

## Knowledge Transfer

For handover and system internals, see:
- [`KNOWLEDGE_TRANSFER.md`](KNOWLEDGE_TRANSFER.md)
- [`ADAPTIVE_SYSTEM_DEEP_DIVE.md`](ADAPTIVE_SYSTEM_DEEP_DIVE.md)

## Tech Stack

- Frontend: React (Vite), Monaco Editor
- Backend: FastAPI, SQLAlchemy
- Database: PostgreSQL
- Execution Engine: Judge0
- AI Engine: Ollama (`qwen2.5-coder:14b`)

## Requirements

- Python 3.10+
- Node.js 18+
- PostgreSQL running with a created database
- Judge0 running and reachable
- Ollama running and reachable

## Environment Variables

Create `backend/.env`:

```env
DATABASE_URL=postgresql+psycopg2://<user>:<password>@<host>:5432/<db_name>
JUDGE0_URL=http://localhost:2358
OLLAMA_URL=http://localhost:11434
```

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

## Local Setup

1. Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Frontend setup

```bash
cd frontend
npm install
```

3. Seed starter problems

```bash
cd backend
source venv/bin/activate
python seed_data.py
```

4. Run the app (from repo root)

```bash
chmod +x run.sh
./run.sh
```

App URLs:
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`

## API Endpoints

- `GET /health`
- `POST /auth/register`
- `POST /auth/login`
- `GET /users/{user_id}`
- `GET /users/{user_id}/progress`
- `GET /users/{user_id}/next-recommendation`
- `GET /problems`
- `GET /problems/{problem_id}`
- `POST /run`
- `POST /validate`
- `POST /submit`
- `POST /feedback`
- `POST /feedback/stream`
- `GET /languages`

## Project Structure

```text
.
├── backend/
│   ├── app.py
│   ├── models.py
│   ├── requirements.txt
│   └── seed_data.py
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
├── QUICKSTART.md
├── run.sh
└── README.md
```

## Notes

- `run.sh` reads `backend/.env` if present and uses those URLs for Judge0 and Ollama.
