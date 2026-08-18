    # AI Tutor Project Working Document

    ## 1. Purpose

    This project is a full-stack coding practice platform where users:
    - register/login,
    - solve programming problems in a web editor,
    - validate code against test cases,
    - submit solutions for scoring and progress updates,
    - receive AI-generated hints.

    ## 2. System Architecture

    - Frontend: React (Vite) in `frontend/`
    - Backend API: FastAPI in `backend/app.py`
    - Database: PostgreSQL via SQLAlchemy models in `backend/models.py`
    - Code execution engine: Judge0 (external service)
    - AI hint engine: Ollama (external service, model `qwen2.5-coder:14b`)

    ## 3. Core Data Model

    Defined in [`backend/models.py`](/home/icfoss/ai tutor versions/AI_Tutor_1/backend/models.py):

    - `User`: account, level, score, solved count
    - `Problem`: coding challenge with difficulty/order/concept mapping
    - `TestCase`: sample/hidden tests with points
    - `Submission`: each user submission with pass/fail + score
    - `Concept`: learning concept metadata
    - `LearnerConceptState`: per-user mastery score per concept

    ## 4. Request Flow (High Level)

    1. User authenticates (`/auth/register` or `/auth/login`).
    2. Frontend loads user progress (`/users/{id}/progress`).
    3. Backend recommends next problem using:
    - unsolved problems,
    - difficulty allowed by user level,
    - concept mastery,
    - recent attempts and failures.
    4. User writes code in Monaco-based editor.
    5. User clicks:
    - `Validate` -> `/validate` (runs all tests, no DB write),
    - `Submit` -> `/submit` (runs all tests + stores submission + updates progress/mastery).
    6. User can request hint -> `/feedback/stream` (streaming AI response from Ollama).

    ## 5. Detailed Runtime Logic

    ### 5.1 Startup

    In [`backend/app.py`](/home/icfoss/ai tutor versions/AI_Tutor_1/backend/app.py), app startup runs `init_db()` which creates missing tables from SQLAlchemy metadata.

    ### 5.2 Authentication

    - `POST /auth/register`
    - Validates username/password length.
    - Stores password with PBKDF2-HMAC-SHA256 + random salt.
    - Initializes user at `beginner`, score `0`, solved `0`.

    - `POST /auth/login`
    - Verifies username exists and password hash matches.
    - Returns serialized user profile.

    ### 5.3 Problem Recommendation

    When frontend requests progress (`GET /users/{user_id}/progress`), backend computes:
    - solved problems,
    - recommendation score for each candidate problem,
    - top-scored next problem + reason string.

    Scoring combines:
    - concept weakness bonus,
    - anti-repetition penalty,
    - productive retry bonus,
    - repeated-failure cooldown,
    - progression fit by `order_index`,
    - spacing bonus since last attempt.

    ### 5.4 Validate vs Submit

    Shared evaluator: `execute_test_cases(problem_id, code, language_id, db)`:
    - fetches all problem test cases,
    - sends each case to Judge0,
    - compares `stdout` with expected output (trimmed),
    - accumulates passed count and points.

    `POST /validate`:
    - runs evaluator only,
    - returns result with `is_validation = true`,
    - does not write `Submission`.

    `POST /submit`:
    - runs evaluator,
    - stores a `Submission`,
    - on first full pass for that problem:
    - increments `problems_solved` and `total_score`,
    - promotes level:
    - `beginner -> intermediate` at 5 solved,
    - `intermediate -> advanced` at 10 solved,
    - updates concept mastery (`+0.08` pass, `-0.04` fail, clamped 0..1),
    - commits transaction.

    ### 5.5 AI Feedback

    - `POST /feedback`: one-shot response from Ollama.
    - `POST /feedback/stream`: streams chunks from Ollama and forwards plain text to frontend.
    - Prompt style changes with learner level (`beginner`, `intermediate`, `advanced`).

    ## 6. Frontend Behavior

    From [`frontend/src/App.jsx`](/home/icfoss/ai tutor versions/AI_Tutor_1/frontend/src/App.jsx) and [`frontend/src/services/api.js`](/home/icfoss/ai tutor versions/AI_Tutor_1/frontend/src/services/api.js):

    - Stores authenticated user in `localStorage` key `auth-user`.
    - Polls `/health` every 15 seconds.
    - Loads progress after login and auto-loads recommended problem.
    - Persists per-problem draft code in `localStorage` (`code-save-{problemId}`).
    - Provides three main actions:
    - Validate
    - Submit
    - Get Hint (streaming)

    ## 7. API Summary

    Main endpoints in current backend:
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

    ## 8. Flow Chart

    ```mermaid
    flowchart TD
        A[User opens frontend] --> B{Authenticated?}
        B -- No --> C[Login/Register form]
        C --> D[POST /auth/login or /auth/register]
        D --> E[Store auth-user in localStorage]
        B -- Yes --> F[Load user progress]
        E --> F
        F --> G[GET /users/{id}/progress]
        G --> H[Backend recommends next problem]
        H --> I[GET /problems/{problem_id}]
        I --> J[User writes code]

        J --> K{Action}
        K -- Validate --> L[POST /validate]
        L --> M[Run all test cases via Judge0]
        M --> N[Return pass/fail + score]
        N --> J

        K -- Submit --> O[POST /submit]
        O --> P[Run all test cases via Judge0]
        P --> Q[Save submission]
        Q --> R{All tests passed?}
        R -- Yes --> S[Update solved count, score, level]
        R -- No --> T[Keep progress unchanged]
        S --> U[Update concept mastery]
        T --> U
        U --> V[Return submission result]
        V --> F

        K -- Get Hint --> W[POST /feedback/stream]
        W --> X[Backend builds level-aware prompt]
        X --> Y[Ollama streams feedback]
        Y --> Z[Frontend appends chunks in Results panel]
        Z --> J
    ```

    ## 9. Environment Dependencies

    Required env values:

    - Backend `.env`
    - `DATABASE_URL`
    - `JUDGE0_URL`
    - `OLLAMA_URL`

    - Frontend `.env`
    - `VITE_API_URL`

    Without Judge0, validate/submit/run endpoints fail.
    Without Ollama, feedback endpoints fail.
    Without PostgreSQL, backend startup and user/problem flows fail.
