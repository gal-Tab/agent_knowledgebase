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

if ! command -v repomix &>/dev/null; then
    echo "Error: repomix is not installed. Run: npm install -g repomix" >&2
    exit 1
fi

if [ -n "$OUTPUT" ]; then
    if [[ "$INPUT" == http* ]]; then
        repomix --remote "$INPUT" --style markdown --output "$OUTPUT"
    else
        repomix "$INPUT" --style markdown --output "$OUTPUT"
    fi
else
    # Write to temp file then cat (repomix requires --output)
    TMPFILE=$(mktemp /tmp/repomix-XXXXXX.md)
    trap "rm -f $TMPFILE" EXIT

    if [[ "$INPUT" == http* ]]; then
        if ! repomix --remote "$INPUT" --style markdown --output "$TMPFILE"; then
            echo "Error: repomix failed for $INPUT" >&2
            exit 1
        fi
    else
        if ! repomix "$INPUT" --style markdown --output "$TMPFILE"; then
            echo "Error: repomix failed for $INPUT" >&2
            exit 1
        fi
    fi
    cat "$TMPFILE"
fi
