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

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if ! git diff --quiet index.html; then
    echo ""
    echo "🚀 GitHub Pages (https://mataki-stack.github.io/tottabi/) へ変更を反映中..."
    git add index.html
    git commit -m "Update video dataset ($(date '+%Y-%m-%d %H:%M'))"
    git push origin main
    echo "✨ GitHub Pages へのアップロードが完了しました！"
  else
    echo ""
    echo "ℹ️ 新着動画の変更はありませんでした（GitHub Pages は最新です）。"
  fi
fi

echo ""
echo "✅ 更新が完了しました！"
echo "🌐 公開URL: https://mataki-stack.github.io/tottabi/"
