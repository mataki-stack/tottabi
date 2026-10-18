from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Any, Callable, Optional

import aiohttp
import yt_dlp

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_CACHE_PATH = DATA_DIR / "raw_cache.json"

CHANNELS = [
    {
        "key": "tottabi",
        "name": "とったび",
        "handle": "@tottabi-twt",
        "channel_id": "UCkNSAQZvGzoPHN2UHE9BWcw",
        "uploads_playlist_id": "UUkNSAQZvGzoPHN2UHE9BWcw",
        "url": "https://www.youtube.com/@tottabi-twt",
    },
    {
        "key": "tottabi_biyori",
        "name": "とったび日和",
        "handle": "@tottabi-vlog",
        "channel_id": "UCKhRskZtvUYiX6cGdhLHpTQ",
        "uploads_playlist_id": "UUKhRskZtvUYiX6cGdhLHpTQ",
        "url": "https://www.youtube.com/@tottabi-vlog",
    },
]

YDL_OPTS = {
    "extract_flat": True,
    "quiet": True,
    "no_warnings": True,
    "ignoreerrors": True,
    "extractor_args": {"youtube": {"lang": ["ja"]}},
}


def _extract_url(url: str) -> dict[str, Any]:
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        info = ydl.extract_info(url, download=False)
        return info or {}


def fetch_channel_structure(
    progress_cb: Optional[Callable[[str, int, int], None]] = None
) -> dict[str, Any]:
    """Use yt-dlp to fetch uploads, shorts, streams, and playlists from both channels."""
    if progress_cb:
        progress_cb("yt-dlpでチャンネルの動画一覧・再生リストを取得中...", 5, 100)

    tasks: list[tuple[str, str, str]] = []
    for ch in CHANNELS:
        tasks.append(("uploads", ch["key"], f"https://www.youtube.com/playlist?list={ch['uploads_playlist_id']}"))
        tasks.append(("shorts", ch["key"], f"https://www.youtube.com/{ch['handle']}/shorts"))
        tasks.append(("streams", ch["key"], f"https://www.youtube.com/{ch['handle']}/streams"))
        tasks.append(("playlists", ch["key"], f"https://www.youtube.com/{ch['handle']}/playlists"))

    results: dict[tuple[str, str], dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_map = {executor.submit(_extract_url, url): (kind, ch_key) for kind, ch_key, url in tasks}
        for future in future_map:
            kind, ch_key = future_map[future]
            try:
                results[(kind, ch_key)] = future.result()
            except Exception as exc:
                print(f"[WARN] Failed to extract {kind} for {ch_key}: {exc}")
                results[(kind, ch_key)] = {}

    if progress_cb:
        progress_cb("yt-dlpで各再生リスト内の動画構成を取得中...", 20, 100)

    # Collect playlists to fetch their entries
    playlist_metas: list[dict[str, Any]] = []
    for ch in CHANNELS:
        pl_tab = results.get(("playlists", ch["key"]), {})
        for idx, entry in enumerate(pl_tab.get("entries") or []):
            if not entry or not entry.get("id"):
                continue
            playlist_metas.append(
                {
                    "id": entry["id"],
                    "title": entry.get("title") or "",
                    "channel_key": ch["key"],
                    "channel_name": ch["name"],
                    "order": idx,
                }
            )

    def _fetch_playlist_items(pl_meta: dict[str, Any]) -> dict[str, Any]:
        pid = pl_meta["id"]
        info = _extract_url(f"https://www.youtube.com/playlist?list={pid}")
        items = []
        for idx, item in enumerate(info.get("entries") or []):
            if not item or not item.get("id"):
                continue
            items.append(
                {
                    "id": item["id"],
                    "title": item.get("title"),
                    "duration": item.get("duration"),
                    "position": idx + 1,
                }
            )
        return {
            **pl_meta,
            "video_ids": [x["id"] for x in items],
            "items": items,
            "count": len(items),
        }

    playlists_data: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        for pl_res in executor.map(_fetch_playlist_items, playlist_metas):
            playlists_data.append(pl_res)

    # Collect videos per channel
    videos_by_id: dict[str, dict[str, Any]] = {}
    shorts_ids: set[str] = set()
    live_ids: set[str] = set()

    for ch in CHANNELS:
        ch_key = ch["key"]
        for entry in (results.get(("shorts", ch_key), {}).get("entries") or []):
            if entry and entry.get("id"):
                shorts_ids.add(entry["id"])
        for entry in (results.get(("streams", ch_key), {}).get("entries") or []):
            if entry and entry.get("id"):
                live_ids.add(entry["id"])

        uploads_entries = results.get(("uploads", ch_key), {}).get("entries") or []
        for idx, entry in enumerate(uploads_entries):
            if not entry or not entry.get("id"):
                continue
            vid = entry["id"]
            if entry.get("title") in (None, "[Private video]", "[Deleted video]", "非公開動画", "削除された動画"):
                continue
            vtype = "short" if vid in shorts_ids or "#shorts" in (entry.get("title") or "").lower() else (
                "live" if vid in live_ids else "video"
            )
            videos_by_id[vid] = {
                "id": vid,
                "title": entry.get("title") or "",
                "duration": entry.get("duration") or 0,
                "channel_key": ch_key,
                "channel_name": ch["name"],
                "channel_id": ch["channel_id"],
                "upload_order": idx,  # 0 is newest in channel
                "video_type": vtype,
                "thumbnail": f"https://i.ytimg.com/vi/{vid}/mqdefault.jpg",
                "thumbnail_hq": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                "url": f"https://www.youtube.com/watch?v={vid}",
            }

    # Also ensure any public video present in a playlist is included
    for pl in playlists_data:
        ch_info = next(c for c in CHANNELS if c["key"] == pl["channel_key"])
        for item in pl["items"]:
            vid = item["id"]
            if vid not in videos_by_id and item.get("title") and item.get("title") not in ("非公開動画", "削除された動画", "[Private video]", "[Deleted video]"):
                videos_by_id[vid] = {
                    "id": vid,
                    "title": item["title"],
                    "duration": item.get("duration") or 0,
                    "channel_key": ch_info["key"],
                    "channel_name": ch_info["name"],
                    "channel_id": ch_info["channel_id"],
                    "upload_order": 99999,
                    "video_type": "video",
                    "thumbnail": f"https://i.ytimg.com/vi/{vid}/mqdefault.jpg",
                    "thumbnail_hq": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                    "url": f"https://www.youtube.com/watch?v={vid}",
                }

    return {
        "videos": videos_by_id,
        "playlists": playlists_data,
        "shorts_ids": list(shorts_ids),
        "live_ids": list(live_ids),
    }


async def _fetch_player_details_batch(
    video_ids: list[str],
    concurrency: int = 35,
    progress_cb: Optional[Callable[[str, int, int], None]] = None,
) -> dict[str, dict[str, Any]]:
    """Fetch full description, exact publishDate, viewCount, lengthSeconds via YouTube innerTube API."""
    sem = asyncio.Semaphore(concurrency)
    details: dict[str, dict[str, Any]] = {}
    total = len(video_ids)
    completed = 0

    connector = aiohttp.TCPConnector(limit=concurrency, ttl_dns_cache=300)
    timeout = aiohttp.ClientTimeout(total=20)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        async def fetch_one(vid: str) -> None:
            nonlocal completed
            payload = {
                "context": {
                    "client": {
                        "clientName": "WEB",
                        "clientVersion": "2.20250101.00.00",
                        "hl": "ja",
                        "gl": "JP",
                    }
                },
                "videoId": vid,
            }
            for attempt in range(3):
                try:
                    async with sem:
                        async with session.post(
                            "https://www.youtube.com/youtubei/v1/player?prettyPrint=false",
                            json=payload,
                        ) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                vd = data.get("videoDetails") or {}
                                mf = (data.get("microformat") or {}).get("playerMicroformatRenderer") or {}
                                pub_raw = mf.get("publishDate") or mf.get("uploadDate") or ""
                                pub_date = pub_raw[:10] if pub_raw else ""
                                details[vid] = {
                                    "title": vd.get("title") or "",
                                    "description": vd.get("shortDescription") or "",
                                    "view_count": int(vd.get("viewCount") or 0),
                                    "duration": int(vd.get("lengthSeconds") or 0),
                                    "publish_timestamp": pub_raw,
                                    "publish_date": pub_date,
                                    "keywords": vd.get("keywords") or [],
                                    "category": mf.get("category") or "",
                                }
                                break
                except Exception:
                    if attempt == 2:
                        break
                    await asyncio.sleep(0.3 * (attempt + 1))

            completed += 1
            if progress_cb and (completed % 50 == 0 or completed == total):
                pct = 30 + int((completed / max(total, 1)) * 60)
                progress_cb(f"各動画の概要欄・公開日・再生回数を取得中 ({completed}/{total})...", pct, 100)

        await asyncio.gather(*(fetch_one(v) for v in video_ids))

    return details


def sync_raw_data(
    force_full: bool = False,
    progress_cb: Optional[Callable[[str, int, int], None]] = None,
) -> dict[str, Any]:
    """Fetch channel structure and merge with cached or newly fetched player details."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    cached: dict[str, Any] = {}
    if RAW_CACHE_PATH.exists():
        try:
            cached = json.loads(RAW_CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            cached = {}

    cached_details: dict[str, dict[str, Any]] = cached.get("player_details") or {}

    structure = fetch_channel_structure(progress_cb=progress_cb)
    all_vids = list(structure["videos"].keys())

    if force_full:
        to_fetch = all_vids
    else:
        # Fetch any video not in cache or missing publish_date, plus newest 30 videos of each channel to update view counts
        newest_vids = [
            v["id"]
            for v in structure["videos"].values()
            if v.get("upload_order", 99999) < 30
        ]
        missing_vids = [
            vid
            for vid in all_vids
            if vid not in cached_details or not cached_details[vid].get("publish_date")
        ]
        to_fetch = list(dict.fromkeys(missing_vids + newest_vids))

    if to_fetch:
        new_details = asyncio.run(
            _fetch_player_details_batch(to_fetch, concurrency=35, progress_cb=progress_cb)
        )
        cached_details.update(new_details)

    raw_data = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "videos": structure["videos"],
        "playlists": structure["playlists"],
        "player_details": cached_details,
    }
    RAW_CACHE_PATH.write_text(
        json.dumps(raw_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return raw_data


if __name__ == "__main__":
    t0 = time.time()
    def _cb(msg: str, cur: int, tot: int) -> None:
        print(f"[{cur:3d}%] {msg}", flush=True)
    data = sync_raw_data(force_full=False, progress_cb=_cb)
    print(f"Done in {time.time() - t0:.1f}s! Total videos: {len(data['videos'])}, Playlists: {len(data['playlists'])}")
