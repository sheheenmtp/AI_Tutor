import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.db import Base, engine
from backend.migration import migrate_database
from backend.routes.auth import router as auth_router
from backend.routes.chat import router as chat_router
from backend.routes.concepts import router as lesson_router
from backend.routes.runner import router as runner_router
from backend.seed import initialize_data

app = FastAPI(title="Linux Adaptive Learning API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(lesson_router)
app.include_router(auth_router)
app.include_router(runner_router)
app.include_router(chat_router)


@app.on_event("startup")
def startup_event():
    migrate_database()
    Base.metadata.create_all(bind=engine, checkfirst=True)
    initialize_data()
    print("Runner route ready: POST /runner/bash")


@app.get("/")
def root():
    return {"detail": "Linux adaptive learning backend is running."}
