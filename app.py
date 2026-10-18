from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import threading
from typing import Any
import webbrowser

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from backend.analyzer import build_enriched_dataset
from backend.fetcher import RAW_CACHE_PATH, sync_raw_data
from backend.storage import (
    VIDEOS_JSON_PATH,
    load_user_state,
    load_videos_dataset,
    save_user_state,
    update_video_user_state,
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="とったび ＆ とったび日和 動画検索ナビ")
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Background sync state
_sync_lock = threading.Lock()
_sync_status: dict[str, Any] = {
    "is_syncing": False,
    "progress": 0,
    "message": "待機中",
    "error": None,
    "last_completed_at": None,
}


class VideoStateUpdateRequest(BaseModel):
    video_id: str
    favorite: bool | None = None
    watched: bool | None = None
    watch_later: bool | None = None
    note: str | None = None


class BulkStateUpdateRequest(BaseModel):
    video_ids: list[str]
    favorite: bool | None = None
    watched: bool | None = None
    watch_later: bool | None = None


class ImportStateRequest(BaseModel):
    favorites: list[str] = []
    watched: list[str] = []
    watch_later: list[str] = []
    notes: dict[str, str] = {}


class SyncRequest(BaseModel):
    force_full: bool = False


def ensure_dataset_ready() -> dict[str, Any]:
    if not VIDEOS_JSON_PATH.exists():
        if RAW_CACHE_PATH.exists():
            return build_enriched_dataset()
        raw = sync_raw_data(force_full=False)
        return build_enriched_dataset(raw)
    return load_videos_dataset()


@app.get("/api/dataset")
def get_dataset() -> JSONResponse:
    dataset = ensure_dataset_ready()
    user_state = load_user_state()
    return JSONResponse({"dataset": dataset, "user_state": user_state})


@app.get("/api/user-state")
def get_user_state() -> dict[str, Any]:
    return load_user_state()


@app.post("/api/user-state/video")
def post_video_user_state(req: VideoStateUpdateRequest) -> dict[str, Any]:
    state = update_video_user_state(
        video_id=req.video_id,
        favorite=req.favorite,
        watched=req.watched,
        watch_later=req.watch_later,
        note=req.note,
    )
    return {"ok": True, "user_state": state}


@app.post("/api/user-state/bulk")
def post_bulk_user_state(req: BulkStateUpdateRequest) -> dict[str, Any]:
    state = load_user_state()
    fav_set = set(state["favorites"])
    watched_set = set(state["watched"])
    later_set = set(state["watch_later"])

    for vid in req.video_ids:
        if req.favorite is not None:
            if req.favorite:
                fav_set.add(vid)
            else:
                fav_set.discard(vid)
        if req.watched is not None:
            if req.watched:
                watched_set.add(vid)
            else:
                watched_set.discard(vid)
        if req.watch_later is not None:
            if req.watch_later:
                later_set.add(vid)
            else:
                later_set.discard(vid)

    state["favorites"] = list(fav_set)
    state["watched"] = list(watched_set)
    state["watch_later"] = list(later_set)
    saved = save_user_state(state)
    return {"ok": True, "user_state": saved}


@app.post("/api/user-state/import")
def import_user_state(req: ImportStateRequest) -> dict[str, Any]:
    saved = save_user_state(
        {
            "favorites": req.favorites,
            "watched": req.watched,
            "watch_later": req.watch_later,
            "notes": req.notes,
        }
    )
    return {"ok": True, "user_state": saved}


@app.get("/api/sync/status")
def get_sync_status() -> dict[str, Any]:
    return _sync_status


@app.post("/api/sync")
def trigger_sync(req: SyncRequest) -> dict[str, Any]:
    if _sync_status["is_syncing"]:
        return {"ok": False, "message": "現在同期処理が実行中です", "status": _sync_status}

    def _run_sync() -> None:
        with _sync_lock:
            _sync_status["is_syncing"] = True
            _sync_status["progress"] = 2
            _sync_status["message"] = "YouTubeから最新データの取得を開始しています..."
            _sync_status["error"] = None
            try:
                def _cb(msg: str, cur: int, tot: int) -> None:
                    _sync_status["progress"] = cur
                    _sync_status["message"] = msg

                raw = sync_raw_data(force_full=req.force_full, progress_cb=_cb)
                _sync_status["progress"] = 95
                _sync_status["message"] = "地域・都道府県・ハネムーンシーズン情報を解析中..."
                build_enriched_dataset(raw)
                _sync_status["progress"] = 100
                _sync_status["message"] = "同期が完了しました！"
                _sync_status["last_completed_at"] = datetime.now(timezone.utc).isoformat()
            except Exception as exc:
                _sync_status["error"] = str(exc)
                _sync_status["message"] = f"エラーが発生しました: {exc}"
            finally:
                _sync_status["is_syncing"] = False

    thread = threading.Thread(target=_run_sync, daemon=True)
    thread.start()
    return {"ok": True, "status": _sync_status}


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def serve_index() -> FileResponse:
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return FileResponse(index_file)


def main() -> None:
    parser = argparse.ArgumentParser(description="とったび＆とったび日和 動画検索Webアプリ")
    parser.add_argument("--host", default="127.0.0.1", help="Host address")
    parser.add_argument("--port", type=int, default=8765, help="Port number")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    parser.add_argument("--sync", action="store_true", help="Sync data from YouTube before starting")
    args = parser.parse_args()

    if args.sync or not VIDEOS_JSON_PATH.exists():
        print("YouTubeから動画データを準備しています...")
        raw = sync_raw_data(force_full=False, progress_cb=lambda m, c, t: print(f"[{c:3d}%] {m}"))
        build_enriched_dataset(raw)

    url = f"http://{args.host}:{args.port}"
    print(f"\n✨ とったび ＆ とったび日和 動画検索ナビを起動しました: {url}\n")
    if not args.no_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
