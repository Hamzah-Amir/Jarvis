import re
from pathlib import Path

# Folder this file lives in (the Jarvis project folder).
# Using this as the base means paths work no matter where you run Python from.
BASE_DIR = Path(__file__).parent

# Model
MODEL = "gemini-3.5-flash-lite"

# Storage paths (Path objects, built from each other with "/")
STORAGE_DIR = BASE_DIR / "storage"
CHATS_DIR = STORAGE_DIR / "chats"
MEMORY_DIR = STORAGE_DIR / "memory"
PROFILE_FILE = MEMORY_DIR / "profile.md"


def slugify(text: str, max_length: int = 40) -> str:
    """Turn text into a safe filename part, e.g. "Who won? Pak vs Iran!" -> "who-won-pak-vs-iran"."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)  # anything not a letter/number becomes "-"
    return text.strip("-")[:max_length].strip("-") or "untitled"
