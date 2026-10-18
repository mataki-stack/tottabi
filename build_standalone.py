"""Build a single self-contained standalone HTML file (index.html) that works offline/via file:// without any server."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from backend.analyzer import clean_description_for_analysis  # noqa: E402

DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"
VIDEOS_JSON_PATH = DATA_DIR / "videos.json"
USER_STATE_PATH = DATA_DIR / "user_state.json"
OUTPUT_HTML_PATH = BASE_DIR / "index.html"


def compact_dataset(raw_dataset: dict) -> dict:
    """Strip repeated footer boilerplate and redundant derived fields to keep standalone HTML lightweight (~1.5 MB)."""
    compacted_videos = []
    for v in raw_dataset.get("videos", []):
        cleaned_desc = clean_description_for_analysis(v.get("description") or "")[0].strip()
        item = {
            "id": v["id"],
            "title": v["title"],
            "channel_key": v["channel_key"],
            "publish_date": v.get("publish_date") or "",
            "duration": v.get("duration") or 0,
            "duration_str": v.get("duration_str") or "-",
            "view_count": v.get("view_count") or 0,
            "video_type": v.get("video_type") or "video",
            "category": v.get("category") or "国内旅・車中泊",
            "location_scope": v.get("location_scope") or "other",
        }
        if cleaned_desc:
            item["description"] = cleaned_desc
        if v.get("excerpt"):
            item["excerpt"] = v["excerpt"]
        if v.get("prefectures"):
            item["prefectures"] = v["prefectures"]
        if v.get("japan_regions"):
            item["japan_regions"] = v["japan_regions"]
        if v.get("overseas_countries"):
            item["overseas_countries"] = v["overseas_countries"]
        if v.get("honeymoon_season_id"):
            item["honeymoon_season_id"] = v["honeymoon_season_id"]
            item["honeymoon_season_title"] = v.get("honeymoon_season_title")
        if v.get("season_episode_label"):
            item["season_episode_label"] = v["season_episode_label"]
        if v.get("playlists"):
            item["playlists"] = v["playlists"]

        compacted_videos.append(item)

    return {
        "updated_at": raw_dataset.get("updated_at"),
        "stats": raw_dataset.get("stats"),
        "channels": raw_dataset.get("channels"),
        "honeymoon_seasons": raw_dataset.get("honeymoon_seasons"),
        "japan_regions": raw_dataset.get("japan_regions"),
        "overseas_countries": raw_dataset.get("overseas_countries"),
        "categories": raw_dataset.get("categories"),
        "years": raw_dataset.get("years"),
        "playlists": raw_dataset.get("playlists"),
        "videos": compacted_videos,
    }


def build_standalone_html() -> Path:
    html_template = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    css_content = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")
    js_content = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    raw_dataset = json.loads(VIDEOS_JSON_PATH.read_text(encoding="utf-8"))
    compacted = compact_dataset(raw_dataset)

    user_state = {"favorites": [], "watched": [], "watch_later": [], "notes": {}}
    if USER_STATE_PATH.exists():
        try:
            user_state = json.loads(USER_STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Escape '</script>' inside JSON strings to prevent early script tag termination
    dataset_json_str = json.dumps(compacted, ensure_ascii=False, separators=(",", ":")).replace(
        "</", "<\\/"
    )
    user_state_json_str = json.dumps(user_state, ensure_ascii=False, separators=(",", ":")).replace(
        "</", "<\\/"
    )

    html_out = html_template.replace(
        '<link rel="stylesheet" href="/static/styles.css" />',
        f"<style>\n{css_content}\n</style>",
    )

    inline_scripts = (
        f"<script>\n"
        f"window.__TOTTABI_DATASET__ = {dataset_json_str};\n"
        f"window.__TOTTABI_USER_STATE__ = {user_state_json_str};\n"
        f"</script>\n"
        f"<script>\n{js_content}\n</script>"
    )
    html_out = html_out.replace('<script src="/static/app.js"></script>', inline_scripts)

    OUTPUT_HTML_PATH.write_text(html_out, encoding="utf-8")
    size_mb = OUTPUT_HTML_PATH.stat().st_size / (1024 * 1024)
    print(f"Built standalone file: {OUTPUT_HTML_PATH} ({size_mb:.2f} MB, {len(compacted['videos'])} videos)")
    return OUTPUT_HTML_PATH


if __name__ == "__main__":
    build_standalone_html()
