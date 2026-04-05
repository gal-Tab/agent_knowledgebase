#!/bin/bash
# Extract git repo to markdown using repomix
# Usage: extract-repo.sh <repo-path-or-url> [output.md]
#
# If output is omitted, writes to stdout.
# Supports both local paths and remote URLs.
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: extract-repo.sh <repo-path-or-url> [output.md]" >&2
    exit 1
fi

INPUT="$1"
OUTPUT="${2:-}"

# Use repomix if installed, fall back to npx
REPOMIX="repomix"
if ! command -v repomix &>/dev/null; then
    if command -v npx &>/dev/null; then
        REPOMIX="npx -y repomix"
    else
        echo "Error: repomix is not installed and npx not available. Run: npm install -g repomix" >&2
        exit 1
    fi
fi

if [ -n "$OUTPUT" ]; then
    if [[ "$INPUT" == http* ]]; then
        $REPOMIX --remote "$INPUT" --style markdown --output "$OUTPUT"
    else
        $REPOMIX "$INPUT" --style markdown --output "$OUTPUT"
    fi
else
    # Write to temp file then cat (repomix requires --output)
    TMPFILE=$(mktemp /tmp/repomix-XXXXXX.md)
    trap "rm -f $TMPFILE" EXIT

    if [[ "$INPUT" == http* ]]; then
        if ! $REPOMIX --remote "$INPUT" --style markdown --output "$TMPFILE"; then
            echo "Error: repomix failed for $INPUT" >&2
            exit 1
        fi
    else
        if ! $REPOMIX "$INPUT" --style markdown --output "$TMPFILE"; then
            echo "Error: repomix failed for $INPUT" >&2
            exit 1
        fi
    fi
    cat "$TMPFILE"
fi
