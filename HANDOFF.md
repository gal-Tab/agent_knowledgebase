# HANDOFF — Compound Learnings (kw-* subsystem)

**Branch:** `feat/compound-learnings` (based on `fix/step6-resolution-prompt`, NOT main)
**Plan (HTML):** `docs/plans/2026-06-08-compound-learnings.html` (local only — `docs/` is gitignored)
**Plan (md, source of truth):** `~/.claude/plans/in-a-new-branch-eager-dragonfly.md`
**Last updated:** 2026-06-08

## What this is

A new `kw-*` subsystem in the `llm-wiki-agent` plugin that captures the agent's own
**work-lessons** (corrections / playbooks / insights / patterns) and resurfaces them
token-frugally, so the agent improves across every project. It lives beside the existing
`kb-*` source-document wiki. Mental model: **kb = ingested sources, kw = the agent's own lessons.**

## Locked design decisions (do not relitigate)

1. **Storage = project-default, global opt-in.** Repo store `.compound/` is primary/committed.
   Global store `~/.claude/compound-knowledge/` (env `COMPOUND_KNOWLEDGE_HOME`, git-init'd) is
   a small curated tier — a lesson goes there ONLY if generalizable AND user-approved. Never a
   dump of every session.
2. **Separate lightweight system**, reusing existing tooling — NOT the `raw/→wiki/` pipeline.
3. **MEMORY boundary:** preferences/behaviors go to MEMORY, never filed as learnings.
4. **Capture:** auto-detect at session end (Stop hook, Phase 3) + manual `/kw-compound`. Always
   approval-gated; never silent-save. Scope defaults to project.
5. **Retrieval = token-frugal:** compact one-line index, grepped not loaded; gated + budgeted
   (≤3 headlines, ~70–90 tokens, deduped per session); bodies on demand; zero overhead when
   no store exists.
6. **Naming:** `kw-*` namespace parallel to `kb-*`.

## Environment note (IMPORTANT for running tests)

- Run tests with **`python3.13 -m pytest -q`** (this interpreter has pytest + PyYAML).
- The default `python3` is 3.14 and needed PyYAML for the CLI subprocess tests:
  `python3 -m pip install --break-system-packages pyyaml` (already done in this env).
- Baseline before this work: 181 tests. After Phase 1: **235 passing.**

## DONE — Phase 1 (write side), all committed + tested

| File | Notes |
|------|-------|
| `lib/learning_format.py` | `validate_learning()`; reuses `ValidationResult`/`VALID_CONFIDENCE`/`parse_frontmatter` from `page_format.py`. Tests: `tests/test_learning_format.py` (19) |
| `lib/slug.py::slug_learning` | id slug from headline. Tests in `tests/test_slug.py` |
| `lib/learning_store.py` | `resolve_stores` (project→global), `write_learning`/`edit_learning` gate, `move_to_archive` (sidecar), `merge_learnings` (project shadows global), `learning_id`, `dest_path`, `TYPE_DIRS`. Tests: `tests/test_learning_store.py` (16) |
| `lib/learning_index.py` | compact index: `format_line`/`parse_line`/`build_index`/`scan_store`/`append_entry`/`rebuild`. Corrections bucket first. Tests: `tests/test_learning_index.py` (12) |
| `tools/learning_index.py` | CLI: `append <file>`, `rebuild [--root]`. Sole owner of `index.md`. |
| `tools/learning_write.py` | CLI: validate→write→index a draft. Tests: `tests/test_learning_write.py` (2) |
| `templates/learning-schema.md`, `templates/learning-template.md` | the contract + skeleton |
| `commands/kw-compound.md` | capture / `--review` / `--audit`; project-default, approval-gated, preferences→MEMORY |
| `.claude-plugin/plugin.json` + `marketplace.json` | bumped to **0.2.0**, description + keywords; commands auto-discovered |
| `README.md` | "Compound Learnings" section |

Store layout (runtime-created): `<root>/{insights,playbooks,corrections,patterns}/<id>.md`,
plus `.archive/` and `.drafts/`; index at `<root>/index.md`. Index line schema:
`- [CODE] id | tags | headline | confidence | date` (codes I/P/C/Pa).

## TODO — Phase 2 (retrieval) — DO THIS NEXT

1. `hooks/kw-surface` (bash, mirror `hooks/kb-status`): UserPromptSubmit hook.
   - Guard: exit 0 if no project/global `index.md` exists.
   - Read prompt from stdin → tokenize → intersect with index tag column → score
     (tag hits + correction bonus). If < threshold (2 hits, or 1 on a correction) → exit 0.
   - Else emit ≤3 headline lines (corrections → score → recency), headline-only, ~70–90 token cap.
   - Per-session dedup via `$TMPDIR/kw-surface-<session>.seen`.
   - Tests: `tests/test_kw_surface_hook.py` (test the parse/gating helper; mirror `tests/test_hook_status.py`).
2. `skills/kw-recall/SKILL.md` — inline read skill (merge both tiers, index-first, ≤5 bodies on
   demand, cite ids). Mirror `skills/kb-query/SKILL.md` frontmatter + `allowed-tools: Read, Glob, Grep`.
3. `hooks/hooks.json` — add `kw-surface prompt` as a SECOND entry in `UserPromptSubmit` (alongside
   `kb-status prompt`); add a `Stop` block invoking `kw-capture stop` (for Phase 3). Each guards
   independently. Current hooks.json structure: arrays of `{hooks:[{type:command, command:"...run-hook.cmd X Y"}]}`.
4. `skills/kb-query/SKILL.md` — after identifying wiki pages, also grep the learnings `index.md`
   (both tiers); surface a matching correction/playbook, read body only if it sharpens the answer
   (within the existing 5-read cap). Keep a router note for pure learning-questions → `kw-recall`.

## TODO — Phase 3 (auto-capture + scale)

5. `hooks/kw-capture` (Stop hook): conservative compoundable-moment detection (user-correction
   language, bug→fix arc, blessed procedure); stage ≤3 drafts in `.drafts/`; print review directive.
   NEVER promotes/silent-saves. Drafts excluded from index.
6. `tools/resolve_learnings.py` + `tests/test_resolve_learnings.py`: dedup-on-write +
   CREATE/UPDATE/SKIP/SUPERSEDE, mirroring `tools/resolve_candidates.py`. "Corrections always win":
   contradicting correction sets old entry `status: superseded` + `superseded_by`, calls
   `learning_store.move_to_archive`, drops it from the index.
7. `commands/kw-compound.md` `--audit`: flesh out staleness sweep + `rebuild`.
8. `skills/kw-researcher/SKILL.md`: planning-time subagent, `Read/Glob/Grep` only (no writes),
   greps both indexes, returns synthesized cited brief in its own token budget.

## Reuse map (mirror, don't reinvent)

- format/validate → `lib/page_format.py`  • write gate → `lib/page_writer.py`  • archive →
  `lib/quarantine.py`  • dedup/supersede → `tools/resolve_candidates.py`  • hooks →
  `hooks/kb-status` + `hooks/run-hook.cmd`  • hook tests → `tests/test_hook_status.py`.

## Verification before claiming done

- `python3.13 -m pytest -q` → all green (235+ as features land).
- E2E: `/kw-compound` files a learning into `.compound/`, one index line, git-staged; `raw/`/`wiki/`/manifest untouched.
- Retrieval: matching prompt injects ≤3 headlines (≤~90 tokens); generic prompt → nothing; same id not re-injected in a session.
- Zero-overhead: no `.compound/` and no global store → both hooks exit 0 silently.
