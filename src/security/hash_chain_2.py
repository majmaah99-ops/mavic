# src/security/hash_chain.py
import hashlib
import json
from pathlib import Path
from datetime import datetime

SALT = "MAVIC-2026-PROD"

def calc_sha256(text: str) -> str:
    salted = f"{SALT}:{text}"
    return hashlib.sha256(salted.encode('utf-8')).hexdigest()

def calc_chain_hash(prev_hash: str, content_hash: str) -> str:
    """سلسلة تدقيق مثل البلوكشين - كما في واجهة MAVIC.pdf"""
    combined = f"{prev_hash}{content_hash}"
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()

def verify_chain(log_path="data/audit_log.jsonl") -> bool:
    log_file = Path(log_path)
    if not log_file.exists():
        return True
    prev = "0"*64
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            expected = calc_chain_hash(prev, entry['content_hash'])
            if expected != entry['chain_hash']:
                return False
            prev = entry['chain_hash']
    return True
