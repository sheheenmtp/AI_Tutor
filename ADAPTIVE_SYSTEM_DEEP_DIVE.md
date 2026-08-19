# Adaptive System Deep Dive

Last updated: April 6, 2026  
Applies to current implementation in `backend/app.py`, `backend/models.py`, `frontend/src/App.jsx`, and `frontend/src/services/api.js`.

## 1. Scope: What "Adaptive System" Means Here

In this project, adaptation happens in four connected layers:

1. Adaptive problem recommendation:
   The backend selects the next problem using learner level, solved history, failures, concept mastery, and progression position.
2. Adaptive progression:
   User level moves from beginner to higher tiers based on solved milestones.
3. Adaptive concept mastery:
   Per-concept mastery score updates after every submit result.
4. Adaptive feedback style:
   AI hint prompt style changes by learner level (`beginner`, `intermediate`, `expert`, `advanced`).

## 2. Runtime Data Sources

The adaptive logic is database-driven, using these tables:

- `users`
  - `current_level`, `problems_solved`, `total_score`
- `submissions`
  - full attempt history, pass/fail status, timestamps
- `problems`
  - `difficulty`, `order_index`, `concept_id`
- `learner_concept_state`
  - per-user, per-concept `mastery_score`
- `concepts`
  - concept metadata linked by `concept_id`

Important:
- `database.json` is not currently read by runtime backend logic.
- Recommendation and mastery state are built from SQL tables, not from the JSON file.

## 3. End-to-End Adaptive Loop

```mermaid
flowchart TD
    A[User registers/logs in] --> B[Frontend calls GET /users/{id}/progress]
    B --> C[Backend computes recommendation score for each candidate]
    C --> D[Frontend loads recommended problem]
    D --> E[User validates or submits]
    E -->|POST /validate| F[Execute tests only; no learner state change]
    E -->|POST /submit| G[Execute tests + store submission]
    G --> H[Update score/solved/level on first full pass]
    G --> I[Update concept mastery pass/fail]
    H --> J[Frontend reloads progress]
    I --> J
    J --> C
```

## 4. Recommendation Engine in Detail

Core function: `build_problem_recommendation(user_id, db)`

### 4.1 Candidate Generation

1. Normalize learner level.
2. Map level to allowed difficulties:
   - `beginner` -> `["beginner"]`
   - `intermediate` -> `["beginner", "intermediate"]`
   - `expert` -> `["beginner", "intermediate", "advanced 1", "advanced_1", "expert"]`
   - `advanced` -> `["beginner", "intermediate", "advanced 1", "advanced_1", "expert", "advanced"]`
3. Exclude already solved problems (`submissions.status == "passed"` distinct by problem).
4. Order remaining candidates by `order_index`.
5. If no candidates remain, return:
   - `problem = None`
   - `reason = "No unsolved problems available for current level"`
   - `score = 0.0`

### 4.2 Learner Context Features

Built before scoring:

- `recent_submissions = latest 10 submissions`
- `recent_problem_set = problems in recent_submissions`
- `recent_fail_set = failed problems in recent_submissions`
- `failed_attempts_by_problem = total historical failed attempts per problem`
- `concept_mastery_cache` from `learner_concept_state`
  - default mastery fallback is `0.7` if concept state is missing
- `last_concept_id` from the most recent submission's problem

Progress anchor (important):

- `submission_progress_anchor`:
  max `order_index` among solved problems (from submission history)
- `profile_progress_anchor`:
  fallback anchor derived from `users.problems_solved` when profile count is ahead of submission history
- `progress_anchor = max(submission_progress_anchor, profile_progress_anchor)`

This prevents legacy/historical users from being routed back to very early problems.

### 4.3 Score Formula (Per Candidate)

Initialize: `score = 0.0`

1. Concept mastery signal:
   - If problem has concept:
     - `mastery = concept_mastery_cache.get(concept_id, 0.7)`
     - `concept_score = (0.7 - mastery) * 60`
     - `score += concept_score`
   - Else:
     - `score += 5` (untagged fallback)

2. Repeat-concept monotony penalty:
   - If candidate concept equals last attempted concept and mastery > 0.55:
     - `score -= 8`

3. Recent attempt penalty:
   - If problem was attempted in last 10 submissions:
     - `score -= 12`

4. Retry/failure shaping:
   - If exactly 1 failed attempt:
     - `score += 6` (productive retry)
   - If failed attempts >= 2:
     - `stall_penalty = min(5 + failed_attempts * 3, 20)`
     - `score -= stall_penalty`
   - Additional cooldown:
     - If in recent_fail_set and failed_attempts >= 2:
       - `score -= 6`

5. Progression fit:
   - `distance = abs(problem.order_index - (progress_anchor + 1))`
   - `progression_bonus = max(0.0, 12 - min(distance, 12))`
   - `score += progression_bonus`

6. Profile lag penalty:
   - Applies only when profile anchor is ahead of submission anchor and candidate is at/before anchor.
   - `lag_penalty = min((progress_anchor - order_index + 1) * 0.6, 8)`
   - `score -= lag_penalty`

7. Spacing bonus:
   - If user attempted this problem before:
     - `hours_since_attempt = now - last_submission_for_problem`
     - `spacing_bonus = min(max(hours_since_attempt / 24, 0), 5)`
     - `score += spacing_bonus`

8. Tiny tie-break toward earlier problems:
   - `score -= order_index * 0.01`

Selection:
- Candidate with highest final score wins.
- Return includes:
  - `problem`
  - `score` (rounded to 2 decimals)
  - `reason` string: semicolon-joined component traces for observability.

## 5. Mastery Update Model

Core function: `update_concept_mastery(user_id, problem_id, passed, db)`

Rules:

1. If problem has no concept, do nothing.
2. If learner has no concept row, create one with `mastery_score = 0.7`.
3. Apply delta:
   - pass -> `+0.08`
   - fail -> `-0.04`
4. Clamp to `[0.0, 1.0]`.
5. Persist on submit transaction commit.
6. Return `mastery_update` payload in `/submit` response.

Behavioral effect:
- Lower mastery increases recommendation score for that concept (via `(0.7 - mastery) * 60`), prioritizing weak areas.

## 6. Progression and Level Adaptation

Progress updates happen in `/submit`, only if all tests pass and this is the first passed submission for that user/problem.

On first full pass:
- `user.problems_solved += 1`
- `user.total_score += submission_score`

Level transitions:
- `beginner -> intermediate` at `>= 5 solved`
- `intermediate -> expert` at `>= 10 solved`
- `expert -> advanced` at `>= 15 solved`

Difficulty unlocks are controlled by level mapping in recommendation candidate filtering.

## 7. Validate vs Submit (Adaptive State Impact)

- `/validate`:
  - Executes all test cases.
  - Returns score/test details.
  - Does not write submission.
  - Does not update score/level/mastery.

- `/submit`:
  - Executes all test cases.
  - Writes submission.
  - May update solved count, total score, level.
  - Always attempts mastery update when problem has concept.

This separation lets learners iterate without changing adaptive state until they commit.

## 8. Adaptive AI Hinting

Adaptation here is prompt-level, not model-switching.

`get_level_guidelines(level)` injects different instructional style:
- Beginner: simple language, minimal jargon, supportive basics.
- Intermediate: structured technical clarity.
- Advanced_1: design/tradeoff focus, practical depth.
- Advanced: concise and analytical, edge-case and efficiency focus.

`build_feedback_prompt(...)` includes:
- learner level
- full problem description
- learner code
- expected output
- actual output

Generation settings are currently fixed:
- model: `qwen2.5-coder:14b`
- `temperature=0.4`, `top_p=0.9`, `num_predict=180`

Streaming endpoint forwards partial chunks to frontend in real time.

## 9. Frontend Integration Points

Frontend adaptation loop behavior:

1. After login, frontend calls `getUserProgress` and auto-loads `next_problem`.
2. After a successful full-pass submit, frontend reloads progress after 1 second.
3. "Next Problem" button loads `progress.next_problem.id` again.
4. Hint request sends learner level from `user.current_level`.

Observed implementation detail:
- `actual_output` sent to feedback currently comes from `runOutput`, which in submit/validate flows is a summary string like:
  - `"Passed X/Y tests · Score A/B"`
- It is not raw testcase stdout, so feedback context is score-oriented rather than per-test raw output.

## 10. Constants and Knobs

Current tuning constants:

- Default mastery baseline: `0.7`
- Concept weight factor: `60`
- Repeat concept penalty: `-8`
- Recent attempt penalty: `-12`
- Untagged fallback bonus: `+5`
- One-failure retry bonus: `+6`
- Stall penalty cap: `20`
- Repeated recent failure cooldown: `-6`
- Progression bonus max: `+12`
- Profile lag penalty cap: `8`
- Spacing bonus max: `+5`
- Tie-break factor: `-order_index * 0.01`
- Mastery pass delta: `+0.08`
- Mastery fail delta: `-0.04`

## 11. Observability and Debugging

Useful response fields:

- `GET /users/{id}/progress`
  - `routing_reason`
  - `routing_score`
  - `next_problem`
- `GET /users/{id}/next-recommendation`
  - `reason`
  - `score`
- `POST /submit`
  - `mastery_update`
  - `passed_tests`, `total_tests`, `score`, `all_passed`

These make the adaptive decision path inspectable without direct DB access.

## 12. Current Limitations

1. No migration framework; schema evolution is manual.
2. Recommendation is rule-based and static-weighted (no learning-to-rank).
3. No authz guard on `user_id` inputs yet.
4. `validate` does not influence adaptive state, which may be intentional but should be explicit in product design.
5. `database.json` may represent richer content but is not part of live adaptive runtime path.

## 13. Safe Places to Modify Adaptive Behavior

- Recommendation math and candidate logic:
  - `build_problem_recommendation(...)` in `backend/app.py`
- Level unlock and milestones:
  - `submit_solution(...)` + `get_allowed_difficulties(...)`
- Concept mastery learning rate:
  - `update_concept_mastery(...)`
- Hint pedagogy by level:
  - `get_level_guidelines(...)` and `build_feedback_prompt(...)`
