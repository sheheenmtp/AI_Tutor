from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
import requests
import os
from dotenv import load_dotenv
from models import init_db, get_db, Problem, TestCase, User, Submission

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

# ================= ENV CONFIG =================
JUDGE0_URL = os.getenv("JUDGE0_URL")
OLLAMA_URL = os.getenv("OLLAMA_URL")

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
    return user

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
    
    return {
        "user": user,
        "solved_problems": solved_ids,
        "next_problem": get_next_problem_for_user(user_id, db)
    }

def get_next_problem_for_user(user_id: int, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    solved = db.query(Submission.problem_id).filter(
        Submission.user_id == user_id,
        Submission.status == "passed"
    ).distinct().all()
    solved_ids = [s[0] for s in solved]
    
    next_problem = db.query(Problem).filter(
        Problem.id.notin_(solved_ids) if solved_ids else True,
        Problem.difficulty.in_(get_allowed_difficulties(user.current_level))
    ).order_by(Problem.order_index).first()
    
    return next_problem

def get_allowed_difficulties(level: str):
    if level == "beginner":
        return ["beginner"]
    elif level == "intermediate":
        return ["beginner", "intermediate"]
    else:
        return ["beginner", "intermediate", "advanced"]

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
    
    # 3. Update User Progress
    if results["all_passed"]:
        user = db.query(User).filter(User.id == req.user_id).first()
        
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
    
    db.commit()
    
    # Add submission ID to results
    results["submission_id"] = submission.id
    results["is_validation"] = False
    return results

# ================= AI FEEDBACK =================
@app.post("/feedback")
def get_ai_feedback(req: FeedbackRequest):

    level_guidelines = get_level_guidelines(req.level)

    prompt = f"""
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
       

@app.get("/languages")
def get_languages():
    try:
        return requests.get(f"{JUDGE0_URL}/languages", timeout=5).json()
    except:
        raise HTTPException(500, "Judge0 not running")
