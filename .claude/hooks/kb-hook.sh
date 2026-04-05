#!/usr/bin/env bash
# LLM Wiki Agent — Knowledge Base Hook
# Called by SessionStart and UserPromptSubmit hooks.
# Scans raw/ for unprocessed files, reads git log, reports wiki stats.
# Output goes to stdout and becomes additionalContext for the agent.
set -eo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
RAW_DIR="$PROJECT_DIR/raw"
WIKI_DIR="$PROJECT_DIR/wiki"
MANIFEST="$RAW_DIR/.manifest.json"

# Track new/updated files as strings (bash 3.2 compatible)
new_files=""
updated_files=""

if [ -d "$RAW_DIR" ]; then
    # Read manifest (or empty object if missing)
    if [ -f "$MANIFEST" ]; then
        manifest=$(cat "$MANIFEST")
    else
        manifest="{}"
    fi

    # Parse manifest once: extract all statuses and hashes in a single python call
    manifest_data=""
    if command -v python3 &>/dev/null; then
        manifest_data=$(echo "$manifest" | python3 -c "
import json, sys
m = json.load(sys.stdin)
for k, v in m.items():
    status = v.get('status', 'missing')
    sha = v.get('sha256', '')
    print(f'{k}\t{status}\t{sha}')
" 2>/dev/null || echo "")
    fi

    # Check each file in raw/ (skip hidden files/dirs)
    for filepath in "$RAW_DIR"/*; do
        [ -f "$filepath" ] || continue
        filename=$(basename "$filepath")

        # Look up status and hash from pre-parsed manifest data
        status="missing"
        stored_hash=""
        if [ -n "$manifest_data" ]; then
            line=$(echo "$manifest_data" | grep "^${filename}"$'\t' || echo "")
            if [ -n "$line" ]; then
                status=$(echo "$line" | cut -f2)
                stored_hash=$(echo "$line" | cut -f3)
            fi
        fi

        if [ "$status" = "missing" ]; then
            new_files="${new_files:+$new_files, }$filename"
        elif [ "$status" = "compiled" ] || [ "$status" = "extracted" ]; then
            # Check if file content changed (sha256 comparison)
            current_hash=$(shasum -a 256 "$filepath" | cut -d' ' -f1)
            if [ "$current_hash" != "$stored_hash" ]; then
                updated_files="${updated_files:+$updated_files, }$filename"
            fi
        fi
    done
fi

# --- Git log (last session) ---
last_session=""
if git -C "$PROJECT_DIR" rev-parse --git-dir &>/dev/null; then
    last_session=$(git -C "$PROJECT_DIR" log --oneline -20 2>/dev/null | grep -E '^[a-f0-9]+ \[session\]' | head -1 || echo "")
fi

# --- Wiki stats ---
sources=0; entities=0; concepts=0; comparisons=0
if [ -d "$WIKI_DIR/sources" ]; then
    sources=$(find "$WIKI_DIR/sources" -name "*.md" -not -name "_index.md" 2>/dev/null | wc -l | tr -d ' ')
fi
if [ -d "$WIKI_DIR/entities" ]; then
    entities=$(find "$WIKI_DIR/entities" -name "*.md" -not -name "_index.md" 2>/dev/null | wc -l | tr -d ' ')
fi
if [ -d "$WIKI_DIR/concepts" ]; then
    concepts=$(find "$WIKI_DIR/concepts" -name "*.md" -not -name "_index.md" 2>/dev/null | wc -l | tr -d ' ')
fi
if [ -d "$WIKI_DIR/comparisons" ]; then
    comparisons=$(find "$WIKI_DIR/comparisons" -name "*.md" -not -name "_index.md" 2>/dev/null | wc -l | tr -d ' ')
fi
total=$((sources + entities + concepts + comparisons))

# --- Output ---
echo "=== KB Status ==="

if [ -n "$new_files" ]; then
    echo "New files in raw/: $new_files"
fi

if [ -n "$updated_files" ]; then
    echo "Updated files: $updated_files"
fi

if [ -z "$new_files" ] && [ -z "$updated_files" ]; then
    echo "No new or updated files in raw/"
fi

if [ -n "$last_session" ]; then
    echo "Last session: $last_session"
else
    echo "Last session: (none)"
fi

echo "Wiki: ${total} pages (${sources}s/${entities}e/${concepts}c/${comparisons}x)"

if [ -f "$PROJECT_DIR/HANDOFF.md" ]; then
    echo "---"
    echo "HANDOFF.md summary:"
    head -20 "$PROJECT_DIR/HANDOFF.md"
fi
