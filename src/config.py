import os
from pathlib import Path


class Settings:
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"
    AUDIT_LOG_PATH = str(DATA_DIR / "audit_log.jsonl")
    SOURCE_HASH_SALT = "mavic-salt-2026"
    MAX_QUERY_LENGTH = 500
    TOP_K_RESULTS = 5
    SIMILARITY_THRESHOLD = 0.2


settings = Settings()
