"""Page format validation for LLM Wiki Agent.

Validates wiki page frontmatter and structure against wiki-schema.md rules.
"""
import re

VALID_TYPES = {"source", "entity", "concept", "comparison"}

# Required frontmatter fields per page type
REQUIRED_FIELDS = {
    "source": {"title", "type", "source_refs", "created", "updated"},
    "entity": {"title", "type", "source_refs", "created", "updated"},
    "concept": {"title", "type", "source_refs", "created", "updated"},
    "comparison": {"title", "type", "source_refs", "created", "updated"},
}

# Optional but expected fields per type
EXPECTED_FIELDS = {
    "source": {"source_file", "source_type", "key_entities", "key_concepts", "tags"},
    "entity": {"aliases", "tags"},
    "concept": {"aliases", "domain_tags", "tags"},
    "comparison": {"compared_entities", "tags"},
}


def parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from a markdown file.

    Expects content starting with '---' and ending with '---'.
    Returns dict of frontmatter fields. Returns empty dict if no frontmatter.
    """
    if not content.startswith("---"):
        return {}

    # Find the closing ---
    end = content.find("---", 3)
    if end == -1:
        return {}

    fm_text = content[3:end].strip()
    result = {}
    current_key = None
    current_list = None

    for line in fm_text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Check for list item (indented with -)
        if stripped.startswith("- ") and current_key is not None:
            if current_list is None:
                current_list = []
                result[current_key] = current_list
            value = stripped[2:].strip().strip('"').strip("'")
            current_list.append(value)
            continue

        # Check for key: value pair
        if ":" in stripped:
            current_list = None
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            current_key = key

            if value == "[]":
                result[key] = []
            elif value == "":
                # Could be a list or empty value — will be populated by subsequent lines
                result[key] = value
            else:
                result[key] = value

    return result


def validate_page(content: str, page_type: str) -> list[str]:
    """Validate a wiki page against schema rules.

    Returns list of error messages. Empty list means valid.
    """
    errors = []

    if page_type not in VALID_TYPES:
        errors.append(f"Invalid page type: '{page_type}'. Must be one of: {VALID_TYPES}")
        return errors

    fm = parse_frontmatter(content)
    if not fm:
        errors.append("Missing or invalid frontmatter (must start with ---)")
        return errors

    # Check required fields
    required = REQUIRED_FIELDS[page_type]
    for field in required:
        if field not in fm:
            errors.append(f"Missing required field: '{field}'")

    # Validate type field matches expected
    if "type" in fm and fm["type"] != page_type:
        errors.append(f"Type mismatch: frontmatter says '{fm['type']}' but expected '{page_type}'")

    # Validate date formats
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    for date_field in ("created", "updated"):
        if date_field in fm and fm[date_field] and not date_pattern.match(str(fm[date_field])):
            errors.append(f"Invalid date format for '{date_field}': '{fm[date_field]}' (expected YYYY-MM-DD)")

    # Check that content has a See Also section
    if "## See Also" not in content:
        errors.append("Missing '## See Also' section (required by wiki-schema.md)")

    return errors


def extract_links(content: str) -> list[tuple[str, str]]:
    """Extract markdown links from content.

    Returns list of (display_text, path) tuples.
    Matches patterns like [Display Text](../category/slug.md)
    """
    pattern = re.compile(r"\[([^\]]+)\]\(([^)]+\.md)\)")
    return pattern.findall(content)
