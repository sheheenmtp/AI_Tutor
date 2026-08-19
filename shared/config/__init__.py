"""Small config helpers placeholder.

Avoid importing heavy dependencies here; keep helpers minimal and testable.
Example usage:

from shared.config import load_dotenv_from_root

"""
from pathlib import Path
from dotenv import load_dotenv


def load_root_env():
    """Load .env at repository root if present."""
    root = Path(__file__).resolve().parents[2]
    env = root / ".env"
    if env.exists():
        load_dotenv(env)
