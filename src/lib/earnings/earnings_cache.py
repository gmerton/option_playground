# src/lib/earnings_cache.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Iterable, List

def _to_dict(obj: Any) -> dict:
    """Handle Polygon models (pydantic) or plain objects."""
    if hasattr(obj, "model_dump"):           # pydantic v2
        return obj.model_dump()
    if hasattr(obj, "dict"):                 # pydantic v1
        return obj.dict()
    if hasattr(obj, "__dict__"):             # generic object
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    raise TypeError(f"Don't know how to serialize: {type(obj)}")

def save_json(items: Iterable[Any], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump([_to_dict(x) for x in items], f, indent=2, ensure_ascii=False)

def load_json(path: str | Path) -> List[dict]:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)
