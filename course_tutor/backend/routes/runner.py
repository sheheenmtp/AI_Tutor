import json
import os
import re
import shlex
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db import SessionLocal
from backend.models import LabTask, PracticeExercise, User
from backend.routes.auth import get_current_user
from backend.schemas import BashRunRequest

router = APIRouter(prefix="/runner", tags=["runner"])

JUDGE0_URL = os.getenv("JUDGE0_URL", "").rstrip("/")
BASH_LANGUAGE_ID = int(os.getenv("JUDGE0_BASH_LANGUAGE_ID", "46"))
BLOCKED_PATTERNS = (
    "$(",
    "`",
    "rm ",
    "mkfs",
    "dd ",
    "shutdown",
    "reboot",
    "curl",
    "wget",
    "nc ",
    "netcat",
    "ssh",
    "scp",
    "sudo",
    "su ",
    "chmod",
    "chown",
    ":(){",
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def post_to_judge0(payload: dict) -> dict:
    if not JUDGE0_URL:
        raise HTTPException(
            status_code=503,
            detail="Judge0 is not configured. Set JUDGE0_URL in the backend environment.",
        )

    query = urlencode(
        {
            "base64_encoded": "false",
            "wait": "true",
            "fields": "stdout,stderr,compile_output,message,status,time,memory",
        }
    )
    request = Request(
        f"{JUDGE0_URL}/submissions?{query}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise HTTPException(status_code=502, detail=f"Judge0 rejected the submission: {detail}") from exc
    except URLError as exc:
        raise HTTPException(status_code=502, detail=f"Judge0 is not reachable at {JUDGE0_URL}") from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail="Judge0 execution timed out") from exc


def command_segments(source_code: str) -> list[str]:
    segments: list[str] = []
    for line in source_code.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        segments.extend(segment.strip() for segment in re.split(r"&&|\|\||[;|]", stripped) if segment.strip())
    return segments


def validate_source_code(source_code: str, allowed_commands: list[str]) -> None:
    lowered = source_code.lower()
    if any(pattern in lowered for pattern in BLOCKED_PATTERNS):
        raise HTTPException(status_code=400, detail="This exercise does not allow that Bash pattern")

    allowed = {command.lower() for command in allowed_commands}
    if not allowed:
        raise HTTPException(status_code=400, detail="This exercise has no allowed commands configured")

    for segment in command_segments(source_code):
        try:
            parts = shlex.split(segment)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Bash command could not be parsed") from exc
        if not parts:
            continue
        command = os.path.basename(parts[0]).lower()
        if command not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"`{command}` is not allowed for this exercise. Allowed commands: {', '.join(sorted(allowed))}",
            )


def resolve_runner_target(payload: BashRunRequest, db: Session) -> tuple[PracticeExercise | LabTask, str]:
    if bool(payload.exercise_id) == bool(payload.lab_task_id):
        raise HTTPException(status_code=400, detail="Choose one practice exercise or one lab task")

    if payload.exercise_id:
        exercise = db.execute(
            select(PracticeExercise).where(PracticeExercise.id == payload.exercise_id)
        ).scalar_one_or_none()
        if not exercise:
            raise HTTPException(status_code=404, detail="Practice exercise not found")
        return exercise, "exercise"

    task = db.execute(select(LabTask).where(LabTask.id == payload.lab_task_id)).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Lab task not found")
    return task, "lab_task"


@router.post("/bash")
def run_bash(
    payload: BashRunRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target, target_type = resolve_runner_target(payload, db)

    source_code = payload.source_code.strip()
    if not source_code:
        raise HTTPException(status_code=400, detail="Bash code is required")
    if len(source_code) > 4000:
        raise HTTPException(status_code=400, detail="Bash code is too long")
    if not command_segments(source_code):
        raise HTTPException(status_code=400, detail="Add a Bash command before running the exercise")
    validate_source_code(source_code, target.allowed_commands or [])

    result = post_to_judge0(
        {
            "language_id": BASH_LANGUAGE_ID,
            "source_code": source_code,
            "stdin": payload.stdin,
            "cpu_time_limit": 2,
            "wall_time_limit": 5,
            "memory_limit": 64000,
        }
    )
    expected_output = (target.expected_output or "").strip()
    stdout = result.get("stdout") or ""
    accepted = result.get("status", {}).get("id") == 3
    result["passed"] = (expected_output in stdout) if expected_output else accepted

    result["target_type"] = target_type
    result["target"] = {
        "id": target.id,
        "title": target.title,
        "expected_output": target.expected_output,
        "allowed_commands": target.allowed_commands or [],
    }
    return result
