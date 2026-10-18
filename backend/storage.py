from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
VIDEOS_JSON_PATH = DATA_DIR / "videos.json"
USER_STATE_PATH = DATA_DIR / "user_state.json"


def _default_user_state() -> dict[str, Any]:
    return {
        "favorites": [],
        "watched": [],
        "watch_later": [],
        "notes": {},
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def load_user_state() -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not USER_STATE_PATH.exists():
        state = _default_user_state()
        save_user_state(state)
        return state
    try:
        data = json.loads(USER_STATE_PATH.read_text(encoding="utf-8"))
        return {
            "favorites": list(dict.fromkeys(data.get("favorites") or [])),
            "watched": list(dict.fromkeys(data.get("watched") or [])),
            "watch_later": list(dict.fromkeys(data.get("watch_later") or [])),
            "notes": dict(data.get("notes") or {}),
            "updated_at": data.get("updated_at") or datetime.now(timezone.utc).isoformat(),
        }
    except Exception:
        return _default_user_state()


def save_user_state(state: dict[str, Any]) -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    normalized = {
        "favorites": list(dict.fromkeys(state.get("favorites") or [])),
        "watched": list(dict.fromkeys(state.get("watched") or [])),
        "watch_later": list(dict.fromkeys(state.get("watch_later") or [])),
        "notes": {k: v for k, v in (state.get("notes") or {}).items() if v and str(v).strip()},
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    USER_STATE_PATH.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return normalized


def update_video_user_state(
    video_id: str,
    favorite: bool | None = None,
    watched: bool | None = None,
    watch_later: bool | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    state = load_user_state()
    fav_set = set(state["favorites"])
    watched_set = set(state["watched"])
    later_set = set(state["watch_later"])

    if favorite is not None:
        if favorite:
            fav_set.add(video_id)
        else:
            fav_set.discard(video_id)

    if watched is not None:
        if watched:
            watched_set.add(video_id)
        else:
            watched_set.discard(video_id)

    if watch_later is not None:
        if watch_later:
            later_set.add(video_id)
        else:
            later_set.discard(video_id)

    if note is not None:
        if note.strip():
            state["notes"][video_id] = note.strip()
        else:
            state["notes"].pop(video_id, None)

    state["favorites"] = list(fav_set)
    state["watched"] = list(watched_set)
    state["watch_later"] = list(later_set)
    return save_user_state(state)


def load_videos_dataset() -> dict[str, Any]:
    if not VIDEOS_JSON_PATH.exists():
        return {"videos": [], "playlists": [], "honeymoon_seasons": [], "stats": {}}
    try:
        return json.loads(VIDEOS_JSON_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"videos": [], "playlists": [], "honeymoon_seasons": [], "stats": {}}


def save_videos_dataset(dataset: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    VIDEOS_JSON_PATH.write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8"
    )
