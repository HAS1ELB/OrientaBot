import json
import re
from typing import Any, Dict, Optional, List

def clamp_float(value: float, min_v: float, max_v: float) -> float:
    return max(min_v, min(max_v, value))

def extract_json_block(text: str) -> Optional[Dict[str, Any]]:
    """
    Extrait le JSON entre <json> ... </json> s'il existe.
    """
    pattern = r"<json>\s*(\{.*?\})\s*</json>"
    match = re.search(pattern, text, flags=re.DOTALL)
    if not match:
        return None
    raw = match.group(1)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None

def safe_float(s: str) -> Optional[float]:
    try:
        return float(s)
    except:
        return None

def trim_history(history: List[Dict[str, str]], max_messages: int = 20) -> List[Dict[str, str]]:
    """
    Limiter l'historique pour rester dans le contexte.
    """
    if len(history) <= max_messages:
        return history
    return history[-max_messages:]