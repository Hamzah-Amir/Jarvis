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

# TTS Configs.
VOICE_MODE = True
VOICE_RATE = 170         
VOICE_VOLUME = 0.9       

# STT Configs
RECORD_SECONDS = 5
SAMPLE_RATE = 16000
STT_MODEL = "whisper-large-v3-turbo"

# Wake word Configs
WAKE_WORD = "hey_jarvis"   # built-in openWakeWord model name
WAKE_THRESHOLD = 0.5       # score 0-1 needed to count as detected (raise if false triggers)
CHUNK = 1280               # samples per mic read = 80 ms at 16 kHz (what openWakeWord expects)
SILENCE_THRESHOLD = 1000   # loudest sample below this = silent recording -> back to standby

def slugify(text: str, max_length: int = 40) -> str:
    """Turn text into a safe filename part, e.g. "Who won? Pak vs Iran!" -> "who-won-pak-vs-iran"."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)  # anything not a letter/number becomes "-"
    return text.strip("-")[:max_length].strip("-") or "untitled"

if __name__ == "__main__":
    pass