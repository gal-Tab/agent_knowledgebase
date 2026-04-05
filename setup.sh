#!/bin/bash
# LLM Wiki Agent — Setup Script
# Installs dependencies and creates directory structure
set -euo pipefail

echo "=== LLM Wiki Agent Setup ==="

# Check for Python 3
if ! command -v python3 &>/dev/null; then
    echo "Error: python3 is required but not found." >&2
    exit 1
fi

# Check for npm (needed for repomix)
if ! command -v npm &>/dev/null; then
    echo "Warning: npm not found. Repo ingestion (repomix) will not be available." >&2
    echo "Install Node.js to enable repo ingestion." >&2
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install --user pymupdf4llm 2>/dev/null \
    || pip install --user pymupdf4llm 2>/dev/null \
    || pip3 install pymupdf4llm 2>/dev/null \
    || { echo "Warning: Could not install pymupdf4llm. Try: pip3 install --user pymupdf4llm" >&2; }

# Install repomix if npm is available (use npx as fallback)
if command -v npm &>/dev/null; then
    echo "Installing repomix..."
    npm install -g repomix 2>/dev/null \
        || { echo "Note: Could not install repomix globally. npx will be used as fallback." >&2; }
fi

# Create directory structure
echo "Creating directory structure..."
mkdir -p raw/.extracted
mkdir -p wiki/sources wiki/entities wiki/concepts wiki/comparisons
mkdir -p tools
mkdir -p .claude/hooks

# Initialize manifest if it doesn't exist
if [ ! -f raw/.manifest.json ]; then
    echo "{}" > raw/.manifest.json
fi

# Initialize wiki index if it doesn't exist
if [ ! -f wiki/index.md ]; then
    cat > wiki/index.md << 'INDEXEOF'
# Wiki Index
Updated: (not yet populated) | Total: 0 pages

## Sources (0)

## Entities (0)

## Concepts (0)

## Comparisons (0)
INDEXEOF
fi

# Make tool scripts executable
chmod +x tools/extract-pdf.py 2>/dev/null || true
chmod +x tools/extract-repo.sh 2>/dev/null || true
chmod +x .claude/hooks/kb-hook.sh 2>/dev/null || true

echo ""
echo "Setup complete."
echo "  - Drop files into raw/ to ingest them"
echo "  - Start a Claude Code session to begin"
