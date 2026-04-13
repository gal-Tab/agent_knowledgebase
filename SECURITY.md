# Security Model — LLM Wiki Agent

## Trust Boundaries

### Trusted
- The Claude Code agent executing compilation
- The wiki-schema.md template (configured by project owner)
- The plugin code (commands, hooks, tools)

### Semi-Trusted
- Raw source files in raw/ (user-provided, could contain adversarial content)
- Extracted markdown in raw/.extracted/ (derived from semi-trusted sources)

### Untrusted
- PDF content (could contain prompt injection attempts in text)
- Git repository content (could contain malicious filenames)
- External tool output (pymupdf4llm, repomix)

## Threat Vectors

### 1. Path Traversal
**Risk:** Malicious filenames like `../../etc/config` could write outside wiki/
**Mitigation:** `security.validate_wiki_path()` resolves and checks all output paths

### 2. Slug Injection
**Risk:** Crafted source titles could produce slugs that escape the wiki directory
**Mitigation:** `security.sanitize_slug()` strips all non-alphanumeric characters

### 3. Denial of Service (Size)
**Risk:** Very large files could exhaust context or disk
**Mitigation:** `security.check_file_size()` warns on files >1MB

### 4. Prompt Injection via Source Content
**Risk:** Source documents could contain text designed to manipulate the compiling agent
**Mitigation:** Limited — the agent processes source content by design. Wiki-schema.md provides guardrails on what pages to create.

### 5. Git History Pollution
**Risk:** Auto-commits could include sensitive data
**Mitigation:** .gitignore audit ensures binaries and extracted files are excluded

## Recommendations
- Run `python3 tools/security.py` periodically to self-test
- Review .gitignore before adding new file types to raw/
- Monitor wiki/ output for unexpected files after compilation
