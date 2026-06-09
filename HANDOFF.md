# HANDOFF — Compound Learnings (kw-* subsystem)

**Branch:** `feat/compound-learnings-phase3` (off `main`; Phases 1+2 landed via PRs #8, #9)
**Plan (HTML):** `docs/plans/2026-06-08-compound-learnings.html` (local only — `docs/` is gitignored)
**Plan (md, source of truth):** `~/.claude/plans/in-a-new-branch-eager-dragonfly.md`
**Last updated:** 2026-06-08 (Phase 3 complete — feature done)

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
4. **Capture:** auto-detect at session end (Stop hook, Phase 3) + manual `/learn-capture`. Always
   approval-gated; never silent-save. Scope defaults to project.
5. **Retrieval = token-frugal:** compact one-line index, grepped not loaded; gated + budgeted
   (≤3 headlines, ~70–90 tokens, deduped per session); bodies on demand; zero overhead when
   no store exists.
6. **Naming:** `kw-*` namespace parallel to `kb-*`.

## Environment note (IMPORTANT for running tests)

- Run tests with **`python3.13 -m pytest -q`** (this interpreter has pytest + PyYAML).
- The default `python3` is 3.14 and needed PyYAML for the CLI subprocess tests:
  `python3 -m pip install --break-system-packages pyyaml` (already done in this env).
- Baseline before this work: 181 tests. After Phase 1: **235 passing.** After Phase 2: **262 passing.** After Phase 3: **292 passing**, then **307** after the QA-driven hardening (user-turn filtering + bash hook tests + CLI tests).

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
| `commands/learn-capture.md` | capture / `--review` / `--audit`; project-default, approval-gated, preferences→MEMORY |
| `.claude-plugin/plugin.json` + `marketplace.json` | bumped to **0.2.0**, description + keywords; commands auto-discovered |
| `README.md` | "Compound Learnings" section |

Store layout (runtime-created): `<root>/{insights,playbooks,corrections,patterns}/<id>.md`,
plus `.archive/` and `.drafts/`; index at `<root>/index.md`. Index line schema:
`- [CODE] id | tags | headline | confidence | date` (codes I/P/C/Pa).

## DONE — Phase 2 (retrieval), all committed + tested (262 passing)

| File | Notes |
|------|-------|
| `lib/learning_surface.py` | pure gating logic: `extract_tokens`, `count_tag_hits`, `qualifies` (≥2 hits, or ≥1 for corrections), `select` (corrections→hits→recency, cap 3, seen-exclusion), `render` (headline-only block), `surface` (merge tiers project-shadows-global → select → render → ids). Tests: `tests/test_learn_surface_hook.py` (27) |
| `hooks/learn-surface` | UserPromptSubmit bash hook. Cheap bash guard (no project/global `index.md` → exit 0, no python). Reads payload via env (stdin owned by heredoc), one python pass → `surface()`, prints ≤3 headlines, records surfaced ids in `$TMPDIR/learn-surface-<session>.seen` for dedup. |
| `hooks/learn-capture` | **Phase 2 stub** — Stop hook wiring in place but detection is a no-op (`exit 0`; guards on `.compound/` absence). Phase 3 fleshes out compoundable-moment detection + draft staging. |
| `hooks/hooks.json` | `learn-surface prompt` added as 2nd `UserPromptSubmit` entry (coexists w/ `wiki-status`, each guards independently); `Stop` block → `learn-capture stop`. |
| `skills/learn-recall/SKILL.md` | index-first read-only recall skill (`Read, Glob, Grep`); merges both tiers, ≤5 bodies on demand, cites ids+scope. |
| `skills/wiki-query/SKILL.md` | new step 3: cheap index-grep of learnings (both tiers), surface matching correction/playbook, body only if it sharpens the answer (within 5-read cap); router note → `learn-recall`. |

Verified: matching prompt injects ≤3 headlines (~43–90 tokens); generic prompt → nothing;
same id not re-injected in a session; no store → both hooks `exit 0` silent; `wiki-status` +
`learn-surface` coexist on `UserPromptSubmit` without interfering.

**Phase 3 note:** `hooks/learn-capture` already exists as a guarded no-op — Phase 3 fills in
detection there (don't recreate it) and wires `tools/resolve_learnings.py`.

## DONE — Phase 3 (auto-capture + scale), all committed + tested (307 passing)

| File | Notes |
|------|-------|
| `lib/learning_capture.py` | pure conservative detector: `extract_user_text` (keep only the human's transcript turns — drops assistant text + tool output so they can't false-trigger), `scan_transcript` (user-correction → correction; blessed → playbook), `scan_git_subjects` (fix/revert → bugfix arc), `detect_signal` (priority correction > playbook > insight; None otherwise). Tests: `tests/test_learn_capture_hook.py` (23) |
| `hooks/learn-capture` | Stop hook, now live. Opt-in guard (`.compound/` must exist), once-per-session throttle (`$TMPDIR/learn-capture-<session>.done`; marker write can't crash the hook), gathers recent git subjects + a user-filtered transcript tail → `detect_signal` → stages ONE draft stub in `.drafts/` on the FIRST signal per session. Never writes a real learning, never indexes, never promotes. (Plan's "≤3 drafts" ceiling; one stub is the conservative choice. Not a true session-end gate — see hook comments.) Bash-level tests: `tests/test_learn_capture_hook_bash.py` (5) |
| `tools/resolve_learnings.py` | dedup-on-write classifier keyed on topic-slug: `classify_learning` → CREATE/UPDATE/SKIP/SUPERSEDE; `supersede()` stamps old `status: superseded`+`superseded_by`, archives, rebuilds index. "Corrections always win." CLI dry-run by default, `--apply` performs archival. Tests: `tests/test_resolve_learnings.py` (14) |
| `commands/learn-capture.md` | Step 3 wired to `resolve_learnings.py`; `--review` handles auto-stubs; `--audit` = rebuild + staleness + contradiction sweep (archive-not-delete). |
| `skills/learn-research/SKILL.md` | planning-time read-only subagent (`Read/Glob/Grep`): sweeps both tiers in its own budget, returns synthesized cited brief (corrections first). |
| `README.md`, `plugin.json`, `marketplace.json` | recall skills documented; bumped to **0.3.0**. |

**Feature complete:** capture (manual + auto) · token-frugal retrieval · dedup/supersede · audit/scale.

## Reuse map (mirror, don't reinvent)

- format/validate → `lib/page_format.py`  • write gate → `lib/page_writer.py`  • archive →
  `lib/quarantine.py`  • dedup/supersede → `tools/resolve_candidates.py`  • hooks →
  `hooks/wiki-status` + `hooks/run-hook.cmd`  • hook tests → `tests/test_hook_status.py`.

## Verification before claiming done

- `python3.13 -m pytest -q` → all green (235+ as features land).
- E2E: `/learn-capture` files a learning into `.compound/`, one index line, git-staged; `raw/`/`wiki/`/manifest untouched.
- Retrieval: matching prompt injects ≤3 headlines (≤~90 tokens); generic prompt → nothing; same id not re-injected in a session.
- Zero-overhead: no `.compound/` and no global store → both hooks exit 0 silently.
