from collections import deque
from typing import Deque, Dict, List, Optional

_MAX_LOGS = 5000
_LOGS: Deque[Dict[str, str]] = deque(maxlen=_MAX_LOGS)


def add_log(entry: Dict[str, str]) -> None:
    _LOGS.append(entry)


def get_logs(filter_term: Optional[str] = None, limit: int = 500) -> List[Dict[str, str]]:
    if limit <= 0:
        return []
    logs = list(_LOGS)
    if filter_term:
        logs = [l for l in logs if filter_term in l.get("message", "")]
    return logs[-limit:]
