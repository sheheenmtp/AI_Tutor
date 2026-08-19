#!/usr/bin/env bash
set -euo pipefail

echo "This script provides helper commands for setting up the monorepo."
echo "It delegates to per-application setup scripts where applicable."

case "${1:-}" in
  pytutor)
    echo "Setup for PyTutor (legacy code moved to pytutor/legacy_py_tutor)"
    if [[ -f "pytutor/legacy_py_tutor/backend/requirements.txt" ]]; then
      (cd pytutor/legacy_py_tutor/backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt)
    fi
    ;;
  course_tutor)
    echo "Setup for Course Tutor"
    if [[ -f "course_tutor/backend/requirements.txt" ]]; then
      (cd course_tutor/backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt)
    fi
    ;;
  *)
    echo "Usage: $0 {pytutor|course_tutor}"
    exit 2
    ;;
esac
