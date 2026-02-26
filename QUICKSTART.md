# Quick Start

## 1. Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL running with a created database
- Judge0 running and reachable
- Ollama running and reachable

## 2. Configure Environment Files

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

## 3. Install Dependencies

Backend:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Frontend:

```bash
cd frontend
npm install
```

## 4. Seed Initial Problems

```bash
cd backend
source venv/bin/activate
python seed_data.py
```

## 5. Run the Platform

From repo root:

```bash
chmod +x run.sh
./run.sh
```

## 6. Open the App

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`

## Common Checks

- Health status: `GET http://localhost:8000/health`
- Judge0 languages: `GET http://localhost:8000/languages`

## Note

Frontend currently uses `userId = 3` in `frontend/src/App.jsx`. Ensure that user exists in your database, or change it.
