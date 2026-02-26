from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
import requests
import os
import json
import hashlib
import hmac
import secrets
import base64
from datetime import datetime
from dotenv import load_dotenv
from models import (
    init_db,
    get_db,
    Problem,
    TestCase,
    User,
    Submission,
    LearnerConceptState,
)

# Load environment variables
load_dotenv()

app = FastAPI(title="Tutor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

# ================= MODELS =================
class RunRequest(BaseModel):
    code: str
    stdin: str = ""
    language_id: int = 71

class SubmitRequest(BaseModel):
    user_id: int
    problem_id: int
    code: str
    language_id: int = 71

class FeedbackRequest(BaseModel):
    level: str
    problem_description: str
    user_code: str
    expected_output: str
    actual_output: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str

# ================= ENV CONFIG =================
JUDGE0_URL = os.getenv("JUDGE0_URL")
OLLAMA_URL = os.getenv("OLLAMA_URL")
AUTH_SALT_BYTES = 16
AUTH_ITERATIONS = 120_000


def serialize_user(user: User):
    return {
        "id": user.id,
        "username": user.username,
        "current_level": user.current_level,
        "total_score": user.total_score,
        "problems_solved": user.problems_solved,
        "created_at": user.created_at
    }


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(AUTH_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, AUTH_ITERATIONS)
    return f"pbkdf2_sha256${AUTH_ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algo, iterations_str, salt_b64, digest_b64 = encoded.split("$")
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iterations_str)
        salt = base64.b64decode(salt_b64.encode())
        expected_digest = base64.b64decode(digest_b64.encode())
    except Exception:
        return False

    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(candidate, expected_digest)

# ================= HELPER FUNCTIONS =================
def get_level_guidelines(level: str) -> str:
    if level == "beginner":
        return """
TONE & COMPLEXITY:
- Use very simple language
- Avoid technical jargon
- Explain concepts like teaching a first-time learner
- Use short sentences
- Focus on basic logic mistakes
- Be very encouraging
"""
    elif level == "intermediate":
        return """
TONE & COMPLEXITY:
- Use correct programming terminology
- Explain logic clearly and structurally
- Mention common patterns or approaches
- Avoid giving full solutions
- Balance encouragement with technical clarity
"""
    else:  # advanced
        return """
TONE & COMPLEXITY:
- Use precise technical language
- Assume strong programming fundamentals
- Focus on edge cases, correctness, and efficiency
- Avoid over-explaining basics
- Keep feedback concise and analytical
"""


def build_feedback_prompt(req: FeedbackRequest) -> str:
    level_guidelines = get_level_guidelines(req.level)
    return f"""
You are an AI hint assistant built into a coding practice platform.
Always address the student as "you." Be direct, clear, and encouraging.
Never exceed 6 sentences. Every sentence must add value — no filler.

Student level: {req.level}
{level_guidelines}

Problem: {req.problem_description}
Their code: {req.user_code}
Expected output: {req.expected_output}
Actual output: {req.actual_output}

Follow this logic:

1. If actual output matches expected output:
   - If hardcoded: call it out in one sentence, explain why it fails in one sentence, give one hint.
   - If genuinely correct: praise one specific thing they did well.

2. If output does not match:
   - One sentence acknowledging what they got right.
   - One sentence pointing to the core mistake conceptually.
   - One sentence guiding question or hint toward the fix.

Rules:
- Never give code or the solution.
- Maximum 10 sentences. No exceptions.
- No bullet points, no headers, no filler phrases.
"""

def execute_test_cases(problem_id: int, code: str, language_id: int, db: Session):
    """
    Helper to run code against all test cases for a problem.
    Returns the results summary and detailed list.
    """
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(404, "Problem not found")
    
    test_cases = db.query(TestCase).filter(TestCase.problem_id == problem_id).all()
    
    results = []
    total_points = 0
    max_points = sum(tc.points for tc in test_cases)
    
    for tc in test_cases:
        try:
            response = requests.post(
                f"{JUDGE0_URL}/submissions?wait=true",
                json={
                    "language_id": language_id,
                    "source_code": code,
                    "stdin": tc.input_data,
                },
                timeout=30
            )
            result = response.json()
            
            actual_output = (result.get("stdout") or "").strip()
            expected_output = tc.expected_output.strip()
            passed = actual_output == expected_output
            
            if passed:
                total_points += tc.points
            
            results.append({
                "test_case_id": tc.id,
                "passed": passed,
                "expected": expected_output,
                "actual": actual_output,
                "points": tc.points if passed else 0,
                "is_sample": tc.is_sample,
                "error": result.get("stderr") or result.get("compile_output")
            })
        except Exception as e:
            results.append({
                "test_case_id": tc.id,
                "passed": False,
                "expected": tc.expected_output,
                "actual": f"Error: {str(e)}",
                "points": 0,
                "is_sample": tc.is_sample,
                "error": str(e)
            })
    
    passed_count = sum(1 for r in results if r["passed"])
    all_passed = passed_count == len(test_cases)
    
    return {
        "status": "passed" if all_passed else "failed",
        "passed_tests": passed_count,
        "total_tests": len(test_cases),
        "score": total_points,
        "max_score": max_points,
        "test_results": results,
        "all_passed": all_passed
    }

# ================= HEALTH CHECK =================
@app.get("/health")
def health():
    status = {"backend": "ok"}
    try:
        requests.get(f"{JUDGE0_URL}/languages", timeout=2)
        status["judge0"] = "ok"
    except:
        status["judge0"] = "offline"
    try:
        requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        status["ollama"] = "ok"
    except:
        status["ollama"] = "offline"
    return status

# ================= USER MANAGEMENT =================
@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    return serialize_user(user)

@app.get("/users/{user_id}/progress")
def get_user_progress(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    solved = db.query(Submission.problem_id).filter(
        Submission.user_id == user_id,
        Submission.status == "passed"
    ).distinct().all()
    solved_ids = [s[0] for s in solved]
    
    recommendation = build_problem_recommendation(user_id, db)

    return {
        "user": serialize_user(user),
        "solved_problems": solved_ids,
        "next_problem": recommendation["problem"],
        "routing_reason": recommendation["reason"],
        "routing_score": recommendation["score"]
    }


@app.post("/auth/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    username = req.username.strip()
    if len(username) < 3:
        raise HTTPException(400, "Username must be at least 3 characters")
    if len(req.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")

    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(409, "Username already exists")

    new_user = User(
        username=username,
        password_hash=hash_password(req.password),
        current_level="beginner",
        total_score=0,
        problems_solved=0
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"user": serialize_user(new_user)}


@app.post("/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    username = req.username.strip()
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.password_hash:
        raise HTTPException(401, "Invalid username or password")

    if not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "Invalid username or password")

    return {"user": serialize_user(user)}

def get_next_problem_for_user(user_id: int, db: Session):
    recommendation = build_problem_recommendation(user_id, db)
    return recommendation["problem"]

def get_allowed_difficulties(level: str):
    if level == "beginner":
        return ["beginner"]
    elif level == "intermediate":
        return ["beginner", "intermediate"]
    else:
        return ["beginner", "intermediate", "advanced"]


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def get_or_create_concept_state(user_id: int, concept_id: str, db: Session):
    state = db.query(LearnerConceptState).filter(
        LearnerConceptState.user_id == user_id,
        LearnerConceptState.concept_id == concept_id
    ).first()
    if state:
        return state

    state = LearnerConceptState(
        user_id=user_id,
        concept_id=concept_id,
        mastery_score=0.7
    )
    db.add(state)
    return state


def update_concept_mastery(user_id: int, problem_id: int, passed: bool, db: Session):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem or not problem.concept_id:
        return None

    state = get_or_create_concept_state(user_id, problem.concept_id, db)
    old_score = state.mastery_score if state.mastery_score is not None else 0.7
    delta = 0.08 if passed else -0.04
    new_score = clamp(old_score + delta, 0.0, 1.0)
    state.mastery_score = new_score

    return {
        "concept_id": problem.concept_id,
        "old_score": round(old_score, 3),
        "new_score": round(new_score, 3),
        "delta": round(delta, 3)
    }


def build_problem_recommendation(user_id: int, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    solved = db.query(Submission.problem_id).filter(
        Submission.user_id == user_id,
        Submission.status == "passed"
    ).distinct().all()
    solved_ids = {s[0] for s in solved}

    user_submissions = db.query(Submission).filter(
        Submission.user_id == user_id
    ).order_by(Submission.submitted_at.desc()).all()

    recent_submissions = user_submissions[:10]
    recent_problem_ids = [s.problem_id for s in recent_submissions]
    recent_failed_ids = [s.problem_id for s in recent_submissions if s.status == "failed"]

    recent_problem_set = set(recent_problem_ids)
    recent_fail_set = set(recent_failed_ids)

    candidate_query = db.query(Problem).filter(
        Problem.difficulty.in_(get_allowed_difficulties(user.current_level))
    )
    if solved_ids:
        candidate_query = candidate_query.filter(Problem.id.notin_(list(solved_ids)))

    candidates = candidate_query.order_by(Problem.order_index).all()
    if not candidates:
        return {
            "problem": None,
            "reason": "No unsolved problems available for current level",
            "score": 0.0
        }

    failed_attempts_by_problem = {}
    for sub in user_submissions:
        if sub.status != "failed":
            continue
        failed_attempts_by_problem[sub.problem_id] = failed_attempts_by_problem.get(sub.problem_id, 0) + 1

    concept_mastery_cache = {}
    for state in db.query(LearnerConceptState).filter(LearnerConceptState.user_id == user_id).all():
        concept_mastery_cache[state.concept_id] = state.mastery_score if state.mastery_score is not None else 0.7

    last_problem = recent_submissions[0].problem_id if recent_submissions else None
    last_problem_obj = db.query(Problem).filter(Problem.id == last_problem).first() if last_problem else None
    last_concept_id = last_problem_obj.concept_id if last_problem_obj else None

    if solved_ids:
        solved_order_indices = db.query(Problem.order_index).filter(Problem.id.in_(list(solved_ids))).all()
        solved_orders = [row[0] for row in solved_order_indices]
        progress_anchor = max(solved_orders) if solved_orders else 0
    else:
        progress_anchor = 0

    now = datetime.utcnow()
    best_problem = None
    best_score = float("-inf")
    best_reason = "Default progression fallback"

    for problem in candidates:
        score = 0.0
        reasons = []

        if problem.concept_id:
            mastery = concept_mastery_cache.get(problem.concept_id, 0.7)
            weakness = 1.0 - mastery
            weakness_score = weakness * 60
            score += weakness_score
            reasons.append(f"weakness +{weakness_score:.1f} (concept {problem.concept_id}, mastery={mastery:.2f})")

            if problem.concept_id == last_concept_id and mastery > 0.55:
                score -= 8
                reasons.append("repeat-concept penalty -8.0 to avoid monotony")

            if problem.id in recent_problem_set:
                score -= 12
                reasons.append("recently attempted penalty -12.0")
        else:
            score += 5
            reasons.append("untagged fallback +5.0")

        failed_attempts = failed_attempts_by_problem.get(problem.id, 0)
        if failed_attempts == 1:
            score += 6
            reasons.append("productive retry bonus +6.0")
        elif failed_attempts >= 2:
            stall_penalty = min(5 + failed_attempts * 3, 20)
            score -= stall_penalty
            reasons.append(f"stall penalty -{stall_penalty:.1f} after {failed_attempts} failed attempts")

        if problem.id in recent_fail_set and failed_attempts >= 2:
            score -= 6
            reasons.append("cooldown penalty -6.0 after recent repeated failure")

        distance_from_anchor = abs(problem.order_index - (progress_anchor + 1))
        progression_bonus = max(0.0, 12 - min(distance_from_anchor, 12))
        score += progression_bonus
        reasons.append(f"progression fit +{progression_bonus:.1f}")

        submission_for_problem = next((s for s in user_submissions if s.problem_id == problem.id), None)
        if submission_for_problem and submission_for_problem.submitted_at:
            hours_since_attempt = (now - submission_for_problem.submitted_at).total_seconds() / 3600
            spacing_bonus = min(max(hours_since_attempt / 24, 0), 5)
            score += spacing_bonus
            reasons.append(f"spacing bonus +{spacing_bonus:.1f}")

        score -= problem.order_index * 0.01

        if score > best_score:
            best_score = score
            best_problem = problem
            best_reason = "; ".join(reasons)

    return {
        "problem": best_problem,
        "reason": best_reason,
        "score": round(best_score, 2)
    }


@app.get("/users/{user_id}/next-recommendation")
def get_next_recommendation(user_id: int, db: Session = Depends(get_db)):
    recommendation = build_problem_recommendation(user_id, db)
    return {
        "next_problem": recommendation["problem"],
        "reason": recommendation["reason"],
        "score": recommendation["score"]
    }

# ================= PROBLEMS =================
@app.get("/problems")
def get_problems(difficulty: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Problem)
    if difficulty:
        query = query.filter(Problem.difficulty == difficulty)
    return query.order_by(Problem.order_index).all()

@app.get("/problems/{problem_id}")
def get_problem(problem_id: int, db: Session = Depends(get_db)):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(404, "Problem not found")
    
    sample_tests = db.query(TestCase).filter(
        TestCase.problem_id == problem_id,
        TestCase.is_sample == True
    ).all()
    
    return {
        "problem": problem,
        "sample_test_cases": sample_tests
    }

# ================= CODE EXECUTION =================
@app.post("/run")
def run_code(req: RunRequest):
    try:
        r = requests.post(
            f"{JUDGE0_URL}/submissions?wait=true",
            json={
                "language_id": req.language_id,
                "source_code": req.code,
                "stdin": req.stdin,
            },
            timeout=30
        )
        return r.json()
    except requests.exceptions.ConnectionError:
        raise HTTPException(500, "Judge0 not running")
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/validate")
def validate_solution(req: SubmitRequest, db: Session = Depends(get_db)):
    """
    Run against all test cases but DO NOT save to database.
    """
    results = execute_test_cases(req.problem_id, req.code, req.language_id, db)
    # Add a flag to indicate this was just validation
    results["is_validation"] = True
    return results

@app.post("/submit")
def submit_solution(req: SubmitRequest, db: Session = Depends(get_db)):
    """
    Run against all test cases AND save submission/update score.
    """
    # 1. Execute Tests
    results = execute_test_cases(req.problem_id, req.code, req.language_id, db)
    
    # 2. Save Submission
    submission = Submission(
        user_id=req.user_id,
        problem_id=req.problem_id,
        code=req.code,
        status=results["status"],
        passed_tests=results["passed_tests"],
        total_tests=results["total_tests"],
        score=results["score"]
    )
    db.add(submission)

    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    # 3. Update User Progress
    if results["all_passed"]:
        # Check if already solved
        previous_pass = db.query(Submission).filter(
            Submission.user_id == req.user_id,
            Submission.problem_id == req.problem_id,
            Submission.status == "passed",
            Submission.id != submission.id
        ).first()
        
        if not previous_pass:
            user.problems_solved += 1
            user.total_score += results["score"]
            
            if user.current_level == "beginner" and user.problems_solved >= 5:
                user.current_level = "intermediate"
            elif user.current_level == "intermediate" and user.problems_solved >= 10:
                user.current_level = "advanced"

    mastery_update = update_concept_mastery(
        user_id=req.user_id,
        problem_id=req.problem_id,
        passed=results["all_passed"],
        db=db
    )
    
    db.commit()
    
    # Add submission ID to results
    results["submission_id"] = submission.id
    results["is_validation"] = False
    if mastery_update:
        results["mastery_update"] = mastery_update
    return results

# ================= AI FEEDBACK =================
@app.post("/feedback")
def get_ai_feedback(req: FeedbackRequest):
    prompt = build_feedback_prompt(req)
    
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": "qwen2.5-coder:14b",
                "prompt": prompt,
                "stream": False,
                "num_predict": 180,
                "temperature": 0.4,
                "top_p": 0.9
            },
            timeout=60
        )
        return {"feedback": r.json().get("response", "")}
    except:
        raise HTTPException(500, "Ollama not running")


@app.post("/feedback/stream")
def get_ai_feedback_stream(req: FeedbackRequest):
    prompt = build_feedback_prompt(req)

    try:
        upstream = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": "qwen2.5-coder:14b",
                "prompt": prompt,
                "stream": True,
                "num_predict": 180,
                "temperature": 0.4,
                "top_p": 0.9
            },
            timeout=120,
            stream=True
        )
        upstream.raise_for_status()
    except Exception:
        raise HTTPException(500, "Ollama not running")

    def stream_chunks():
        try:
            for line in upstream.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue

                chunk = payload.get("response", "")
                if chunk:
                    yield chunk

                if payload.get("done", False):
                    break
        finally:
            upstream.close()

    return StreamingResponse(stream_chunks(), media_type="text/plain; charset=utf-8")


@app.get("/languages")
def get_languages():
    try:
        return requests.get(f"{JUDGE0_URL}/languages", timeout=5).json()
    except:
        raise HTTPException(500, "Judge0 not running")
