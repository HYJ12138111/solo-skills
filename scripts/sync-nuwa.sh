#!/bin/bash
# Auto-sync nuwa skill from upstream alchaincyf/nuwa-skill
set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

echo "[$(date '+%Y-%m-%d %H:%M')] Syncing nuwa from alchaincyf/nuwa-skill..."

# Shallow clone upstream
git clone --depth 1 https://github.com/alchaincyf/nuwa-skill.git "$TMPDIR" 2>&1

# Get upstream version hash
UPSTREAM_VER=$(git -C "$TMPDIR" log -1 --format='%H')

# Check if we already have this version
if [ -f skills/nuwa/.upstream-version ] && grep -q "$UPSTREAM_VER" skills/nuwa/.upstream-version 2>/dev/null; then
    echo "  Already up to date ($(git -C "$TMPDIR" log -1 --format='%h %s'))."
    exit 0
fi

echo "  Upstream: $(git -C "$TMPDIR" log -1 --format='%h %s')"

# Replace nuwa skill files
rm -rf skills/nuwa
cp -a "$TMPDIR"/. skills/nuwa/

# Remove upstream git metadata
rm -rf skills/nuwa/.git skills/nuwa/.github 2>/dev/null || true

# Save version marker
echo "$UPSTREAM_VER" > skills/nuwa/.upstream-version

# Commit if changed
git add skills/nuwa/

if git diff --staged --quiet && git diff --quiet; then
    echo "  No file changes."
    exit 0
fi

git commit -m "auto-sync: nuwa from alchaincyf/nuwa-skill ($(date '+%Y-%m-%d'))" 2>&1
git push origin main 2>&1

echo "[$(date '+%Y-%m-%d %H:%M')] nuwa sync complete."
