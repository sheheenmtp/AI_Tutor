"""Shim entrypoint that delegates to the existing py_tutor backend.

This inserts the legacy backend directory onto `sys.path` and imports the
original `app` module. Run with `uvicorn pytutor.backend.app:app` to start
the existing PyTutor backend without moving files.
"""
import os
import sys

HERE = os.path.dirname(__file__)
# Path to the original backend implementation (moved into `pytutor/legacy_py_tutor`)
LEGACY_BACKEND = os.path.normpath(os.path.join(HERE, '..', '..', 'pytutor', 'legacy_py_tutor', 'backend'))
if LEGACY_BACKEND not in sys.path:
    sys.path.insert(0, LEGACY_BACKEND)

# The legacy module expects to be run from its folder; importing its `app`
# object into this module lets uvicorn locate `app` as `pytutor.backend.app:app`.
from app import app  # type: ignore

__all__ = ["app"]
