#!/usr/bin/env zsh
set -e

cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

uv run python app.py "$@"
