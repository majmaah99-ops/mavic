# src/security/audit_log.py
import json
from pathlib import Path
from datetime import datetime
from .hash_chain import calc_sha256, calc_chain_hash

LOG_PATH = Path("data/audit_log.jsonl")

def log_query(query: str, results: list, trust: int):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # احسب prev_hash
    prev_hash = "0"*64
    if LOG_PATH.exists():
        try:
            with open(LOG_PATH, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    last = json.loads(lines[-1])
                    prev_hash = last['chain_hash']
        except:
            pass

    content = f"{query}|{trust}|{len(results)}"
    content_hash = calc_sha256(content)
    chain_hash = calc_chain_hash(prev_hash, content_hash)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "trust": trust,
        "sources_count": len(results),
        "content_hash": content_hash,
        "chain_hash": chain_hash,
        "prev_hash": prev_hash
    }
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    return entry

def get_audit_count():
    if not LOG_PATH.exists():
        return 0
    with open(LOG_PATH, 'r', encoding='utf-8') as f:
        return len(f.readlines())
