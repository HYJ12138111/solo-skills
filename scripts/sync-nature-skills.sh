#!/bin/bash
# Auto-sync nature skills from upstream Yuan1z0825/nature-skills
set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

echo "[$(date '+%Y-%m-%d %H:%M')] Checking for nature-skills updates..."

git fetch upstream 2>&1

LOCAL=$(git rev-parse HEAD)
UPSTREAM=$(git rev-parse upstream/main)

if [ "$LOCAL" = "$UPSTREAM" ]; then
    echo "  Already up to date."
    exit 0
fi

echo "  New commits detected, syncing nature skills..."

# Pull all nature skills from upstream
NATURE_SKILLS=$(git ls-tree --name-only upstream/main -- skills/nature-* 2>/dev/null | xargs -I{} dirname {} | sort -u || true)

if [ -n "$NATURE_SKILLS" ]; then
    git checkout upstream/main -- skills/nature-* skills/_shared/ 2>&1
else
    echo "  No nature skills found in upstream."
    exit 0
fi

# Check if there are changes to commit
if git diff --staged --quiet && git diff --quiet; then
    echo "  No file changes (merge commits only)."
    exit 0
fi

git commit -m "auto-sync: nature skills from upstream ($(date '+%Y-%m-%d'))" 2>&1
git push origin main 2>&1

echo "[$(date '+%Y-%m-%d %H:%M')] Sync complete."
