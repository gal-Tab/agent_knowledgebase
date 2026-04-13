"""Parser for kb-status hook output.

Parses the structured output of the kb-status hook into a dict
for programmatic consumption.
"""
import re


def parse_hook_output(output_text: str) -> dict:
    """Parse kb-status hook output into structured data.

    Returns dict with:
        - has_header: bool (whether output contains '=== KB Status ===')
        - new_files: list[str]
        - updated_files: list[str]
        - pending_files: list[str]
        - has_work: bool
        - action: str or None
        - last_session: str or None
        - wiki_stats: dict with keys: total, sources, entities, concepts, comparisons
    """
    result = {
        "has_header": False,
        "new_files": [],
        "updated_files": [],
        "pending_files": [],
        "has_work": False,
        "action": None,
        "last_session": None,
        "wiki_stats": {
            "total": 0,
            "sources": 0,
            "entities": 0,
            "concepts": 0,
            "comparisons": 0,
        },
    }

    if not output_text or not output_text.strip():
        return result

    for line in output_text.strip().split("\n"):
        line = line.strip()

        if line == "=== KB Status ===":
            result["has_header"] = True
            continue

        if line.startswith("New files in raw/: "):
            files = line[len("New files in raw/: "):]
            result["new_files"] = [f.strip() for f in files.split(",") if f.strip()]
            result["has_work"] = True
            continue

        if line.startswith("Updated files: "):
            files = line[len("Updated files: "):]
            result["updated_files"] = [f.strip() for f in files.split(",") if f.strip()]
            result["has_work"] = True
            continue

        if line.startswith("Pending compilation: "):
            files = line[len("Pending compilation: "):]
            result["pending_files"] = [f.strip() for f in files.split(",") if f.strip()]
            result["has_work"] = True
            continue

        if line.startswith("ACTION:") or line.startswith("New files are waiting"):
            result["action"] = line
            continue

        if line.startswith("Last session: "):
            value = line[len("Last session: "):]
            result["last_session"] = None if value == "(none)" else value
            continue

        # Wiki stats: "Wiki: 35 pages (15s/12e/6c/2x)"
        wiki_match = re.match(
            r"Wiki:\s*(\d+)\s*pages?\s*\((\d+)s/(\d+)e/(\d+)c/(\d+)x\)", line
        )
        if wiki_match:
            result["wiki_stats"] = {
                "total": int(wiki_match.group(1)),
                "sources": int(wiki_match.group(2)),
                "entities": int(wiki_match.group(3)),
                "concepts": int(wiki_match.group(4)),
                "comparisons": int(wiki_match.group(5)),
            }

    return result
