#!/usr/bin/env bash
cd "$(dirname "$0")"
./update.sh
echo ""
read -n 1 -s -r -p "何かキーを押すとウィンドウを閉じます..."
