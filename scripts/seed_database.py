"""Helper wrapper to run seed scripts for each application."""
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent

def run_pytutor_seed():
    seed = root / "pytutor" / "legacy_py_tutor" / "backend" / "seed_data.py"
    if seed.exists():
        subprocess.check_call([sys.executable, str(seed)])

def run_course_tutor_seed():
    seed = root / "course_tutor" / "backend" / "seed.py"
    if seed.exists():
        subprocess.check_call([sys.executable, str(seed)])

if __name__ == "__main__":
    run_pytutor_seed()
    run_course_tutor_seed()
