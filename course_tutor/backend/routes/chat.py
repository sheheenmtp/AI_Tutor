import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.db import SessionLocal
from backend.models import User
from backend.routes.auth import get_current_user
from backend.routes.concepts import get_lesson_content, get_lesson_model
from backend.schemas import TeacherChatRequest, TeacherChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])

OLLAMA_URL = os.getenv("OLLAMA_URL", "").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:14b")

TEACHER_SYSTEM_PROMPT = """
You are a helpful Linux course teacher inside an adaptive learning platform.

Teaching style:
- Be patient, clear, and practical.
- Use the current lesson context first.
- Explain Linux and Bash ideas step by step.
- Ask one short follow-up question when the learner seems stuck.
- Keep answers concise unless the learner asks for detail.

Safety and assessment rules:
- Do not reveal quiz answers directly before submission.
- For labs and Bash practice, give hints first. If a learner asks for the exact command, explain the reasoning and provide the smallest useful command.
- Do not suggest destructive commands such as rm, mkfs, dd, shutdown, reboot, sudo, chmod, or chown.
- If the user asks something outside this Linux course, briefly redirect back to the lesson.
""".strip()


def require_ollama_url() -> str:
    if not OLLAMA_URL:
        raise HTTPException(
            status_code=503,
            detail="Ollama is not configured. Set OLLAMA_URL in the backend environment.",
        )
    return OLLAMA_URL


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def clamp_text(value: str, limit: int) -> str:
    text = (value or "").strip()
    return text[:limit]


def ollama_chat(messages: list[dict[str, str]]) -> str:
    ollama_url = require_ollama_url()
    request = Request(
        f"{ollama_url}/api/chat",
        data=json.dumps(
            {
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.35,
                    "num_ctx": 8192,
                },
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=90) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise HTTPException(status_code=502, detail=f"Ollama rejected the request: {detail}") from exc
    except URLError as exc:
        raise HTTPException(status_code=502, detail=f"Ollama is not reachable at {OLLAMA_URL}") from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail="Ollama response timed out") from exc

    reply = payload.get("message", {}).get("content", "").strip()
    if not reply:
        raise HTTPException(status_code=502, detail="Ollama returned an empty response")
    return reply


def build_teacher_messages(payload: TeacherChatRequest, db: Session) -> list[dict[str, str]]:
    question = clamp_text(payload.message, 2000)
    if not question:
        raise HTTPException(status_code=400, detail="Message is required")

    lesson = get_lesson_model(db, payload.lesson_id)
    content = get_lesson_content(db, lesson.id, payload.level or "standard")
    if not content:
        content = get_lesson_content(db, lesson.id, "standard")
    if not content:
        raise HTTPException(status_code=404, detail="Lesson content not found")

    lesson_context = f"""
Course: {lesson.topic.module.course.title}
Module: {lesson.topic.module.title}
Topic: {lesson.topic.title}
Lesson: {lesson.title}
Current view: {payload.view or "lesson"}
Lab: {payload.lab_title or "none"}

Lesson content:
{clamp_text(content.content, 6000)}
""".strip()

    messages: list[dict[str, str]] = [
        {"role": "system", "content": TEACHER_SYSTEM_PROMPT},
        {"role": "system", "content": lesson_context},
    ]

    for item in payload.history[-8:]:
        role = item.role if item.role in {"user", "assistant"} else "user"
        text = clamp_text(item.content, 1200)
        if text:
            messages.append({"role": role, "content": text})

    messages.append({"role": "user", "content": question})
    return messages


def open_ollama_stream(messages: list[dict[str, str]]):
    ollama_url = require_ollama_url()
    request = Request(
        f"{ollama_url}/api/chat",
        data=json.dumps(
            {
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": 0.35,
                    "num_ctx": 8192,
                },
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        return urlopen(request, timeout=90)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise HTTPException(status_code=502, detail=f"Ollama rejected the request: {detail}") from exc
    except URLError as exc:
        raise HTTPException(status_code=502, detail=f"Ollama is not reachable at {OLLAMA_URL}") from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail="Ollama response timed out") from exc


def stream_ollama_response(response):
    try:
        for raw_line in response:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            payload = json.loads(line)
            if payload.get("error"):
                yield f"\nTeacher error: {payload['error']}"
                break
            chunk = payload.get("message", {}).get("content", "")
            if chunk:
                yield chunk
            if payload.get("done"):
                break
    finally:
        response.close()


@router.post("/teacher", response_model=TeacherChatResponse)
def teacher_chat(
    payload: TeacherChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ = current_user
    messages = build_teacher_messages(payload, db)
    reply = ollama_chat(messages)
    return TeacherChatResponse(reply=reply, model=OLLAMA_MODEL)


@router.post("/teacher/stream")
def teacher_chat_stream(
    payload: TeacherChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ = current_user
    messages = build_teacher_messages(payload, db)
    response = open_ollama_stream(messages)
    return StreamingResponse(
        stream_ollama_response(response),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
