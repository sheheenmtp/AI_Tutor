# Content Authoring Guide

## Purpose

Generated lesson files in `Data/generated/` are intended to feed the newer lesson-based course model. Each file represents one lesson under an existing topic and can include:

- Lesson metadata.
- Three explanation levels.
- Ten MCQ questions per level.
- Optional Bash practice exercise.
- Optional guided lab.

Use `backend/content_importer.py` to validate and import these files.

## Minimal File Shape

```json
{
  "topic_slug": "introduction-to-userspace",
  "module_slug": "what-userspace-is",
  "lesson": {
    "title": "Why Userspace Matters",
    "slug": "why-userspace-matters",
    "sequence": 1,
    "lesson_type": "concept",
    "difficulty": "beginner",
    "objective": "Understand why userspace is separated from kernelspace.",
    "practice_task": null,
    "tags": ["userspace", "security"],
    "common_confusions": [],
    "examples": [],
    "levels": {
      "standard": {
        "explanation": "## Lesson title\n\nLesson body...",
        "questions": []
      },
      "layman": {
        "explanation": "## Lesson title\n\nSimpler body...",
        "questions": []
      },
      "eli10": {
        "explanation": "## Lesson title\n\nVery simple body...",
        "questions": []
      }
    }
  }
}
```

`module_slug` is optional only when `topic_slug` is unique across the database.

## Required Levels

Every lesson must include exactly these level keys:

- `standard`
- `layman`
- `eli10`

Each level needs:

- `explanation`: non-empty Markdown string.
- `questions`: exactly 10 questions.

## Question Rules

Each question must have:

```json
{
  "question": "What is userspace used for?",
  "options": [
    "Running normal applications safely",
    "Directly managing CPU wiring",
    "Replacing the bootloader",
    "Physically storing RAM"
  ],
  "answer": "Running normal applications safely",
  "explanation": "Userspace is where normal apps and commands run.",
  "difficulty": "easy"
}
```

Rules enforced by the importer:

- `question` must be non-empty.
- `options` must contain exactly four non-empty strings.
- `answer` must exactly match one option.
- `explanation` is optional but recommended.
- `difficulty` defaults to `medium` if omitted.

## Optional Practice Exercise

```json
{
  "practice_exercise": {
    "title": "Print a userspace clue",
    "prompt": "Use Bash to print a sentence that includes the word userspace.",
    "starter_code": "# Write an echo command\n",
    "expected_output": "userspace",
    "allowed_commands": ["echo"],
    "is_required": false
  }
}
```

Rules:

- `allowed_commands` must be non-empty.
- Only safe commands are accepted by the importer.
- `starter_code` must not reveal the expected answer.
- `expected_output` is used as a substring check against `stdout`.

Safe commands currently allowed by the importer:

```text
cat, cd, date, echo, head, id, ls, mkdir, printf, ps, pwd, touch, whoami
```

Note: `backend/seed.py` contains a legacy default list that includes `grep`, but `content_importer.py` does not currently allow `grep`. Keep generated content aligned with `content_importer.py`.

## Optional Lab

```json
{
  "lab": {
    "title": "Lab: Basic Linux Observation Commands",
    "description": "Practice safe commands in a guided environment.",
    "sequence": 1,
    "is_required": false,
    "tasks": [
      {
        "title": "Print Working Directory",
        "instruction": "Run a command that prints the current working directory.",
        "starter_code": "# Print the current directory\n",
        "expected_output": "/",
        "allowed_commands": ["pwd"],
        "validation": null
      }
    ]
  }
}
```

Rules:

- A lab must contain at least one task.
- Each task needs title, instruction, starter code, and allowed commands.
- `validation` may be a JSON object, but current runner behavior mainly uses `expected_output`.

## Validation Commands

Validate all generated files without writing:

```bash
python -m backend.content_importer --dry-run Data/generated
```

Validate one file:

```bash
python -m backend.content_importer --dry-run Data/generated/M1T1_1.json
```

Import all generated files:

```bash
python -m backend.content_importer Data/generated
```

## Authoring Quality Checklist

Before importing a lesson:

- Each level teaches the same objective at a different clarity level.
- The `standard` version uses accurate Linux terminology.
- The `layman` version simplifies without becoming misleading.
- The `eli10` version avoids jargon or explains it immediately.
- Questions test understanding, not wording recall only.
- Wrong options are plausible but clearly incorrect.
- Answers exactly match one option.
- Practice/lab starter code gives a scaffold but not the answer.
- Allowed commands are minimal for the task.
- No destructive commands are suggested in explanations, practice, labs, or teacher prompts.

