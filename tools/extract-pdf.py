#!/usr/bin/env python3
"""Extract PDF to clean markdown using pymupdf4llm.

Usage: extract-pdf.py <input.pdf> [output.md]
  If output is omitted, writes to stdout.
"""
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: extract-pdf.py <input.pdf> [output.md]", file=sys.stderr)
        sys.exit(1)

    import pymupdf4llm

    input_path = sys.argv[1]
    try:
        md = pymupdf4llm.to_markdown(input_path)
    except Exception as e:
        print(f"Error extracting {input_path}: {e}", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) >= 3:
        with open(sys.argv[2], "w", encoding="utf-8") as f:
            f.write(md)
    else:
        print(md)

if __name__ == "__main__":
    main()
