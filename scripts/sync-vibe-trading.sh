#!/bin/bash
# Auto-sync vibe-trading skill from upstream HKUDS/Vibe-Trading
set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

echo "[$(date '+%Y-%m-%d %H:%M')] Syncing vibe-trading from HKUDS/Vibe-Trading..."

# Get latest commit SHA via GitHub API (no clone needed)
UPSTREAM_SHA=$(curl -s "https://api.github.com/repos/HKUDS/Vibe-Trading/commits/main" | python3 -c "import sys,json; print(json.load(sys.stdin)['sha'])" 2>/dev/null)
if [ -z "$UPSTREAM_SHA" ]; then
    echo "  Failed to reach GitHub API, skipping."
    exit 0
fi

# Check if already up to date
if [ -f skills/vibe-trading/.upstream-version ] && grep -q "$UPSTREAM_SHA" skills/vibe-trading/.upstream-version 2>/dev/null; then
    echo "  Already up to date ($UPSTREAM_SHA)."
    exit 0
fi

# Fetch SKILL.md
curl -sL "https://raw.githubusercontent.com/HKUDS/Vibe-Trading/main/agent/SKILL.md" -o /tmp/vibe_skill.md 2>&1
if [ ! -s /tmp/vibe_skill.md ]; then
    echo "  Failed to fetch SKILL.md, skipping."
    exit 0
fi

# Fetch ashare-mootdx references
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR /tmp/vibe_skill.md" EXIT

curl -sL "https://raw.githubusercontent.com/HKUDS/Vibe-Trading/main/agent/skills/ashare-mootdx/references/a_mootdx_fetcher.py" -o "$TMPDIR/a_mootdx_fetcher.py" 2>&1

# Check for differences
cp /tmp/vibe_skill.md "$TMPDIR/SKILL.md"

if [ -d skills/vibe-trading ]; then
    # Compare existing vs upstream
    if diff -rq skills/vibe-trading/ashare-mootdx/references/ "$TMPDIR/" 2>/dev/null | grep -q differ; then
        HAS_DIFF=1
    else
        HAS_DIFF=0
    fi
    if ! diff -q skills/vibe-trading/SKILL.md /tmp/vibe_skill.md > /dev/null 2>&1; then
        HAS_DIFF=1
    fi
else
    HAS_DIFF=1
fi

if [ "$HAS_DIFF" = "0" ]; then
    echo "  No file changes."
    echo "$UPSTREAM_SHA" > skills/vibe-trading/.upstream-version
    exit 0
fi

echo "  Upstream SHA: ${UPSTREAM_SHA:0:7}"

# Replace files
rm -rf skills/vibe-trading
mkdir -p skills/vibe-trading/ashare-mootdx/references
cp /tmp/vibe_skill.md skills/vibe-trading/SKILL.md
cp "$TMPDIR/a_mootdx_fetcher.py" skills/vibe-trading/ashare-mootdx/references/

# Save version marker
echo "$UPSTREAM_SHA" > skills/vibe-trading/.upstream-version

# Commit if changed
git add skills/vibe-trading/

if git diff --staged --quiet && git diff --quiet; then
    echo "  No file changes."
    exit 0
fi

git commit -m "auto-sync: vibe-trading from HKUDS/Vibe-Trading ($(date '+%Y-%m-%d'))" 2>&1
git push origin main 2>&1

echo "[$(date '+%Y-%m-%d %H:%M')] vibe-trading sync complete."
