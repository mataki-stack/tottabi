#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

UV_BIN="${HOME}/.local/bin/uv"
if ! command -v "$UV_BIN" >/dev/null 2>&1; then
  UV_BIN="uv"
fi

echo "=================================================="
echo " 🚐 とったび & とったび日和 最新動画データの取得・更新"
echo "=================================================="

"$UV_BIN" run python -c "
from backend.fetcher import sync_all_channels
from backend.analyzer import build_analyzed_dataset
from build_standalone import build_standalone_html

def on_prog(msg, pct):
    print(f'[{pct:3d}%] {msg}')

raw = sync_all_channels(progress_callback=on_prog, force_full=False)
build_analyzed_dataset(raw)
build_standalone_html()
"

echo ""
echo "✅ 更新が完了しました！ index.html をブラウザで開いてご覧ください。"
