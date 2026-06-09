---
description: Capture work-lessons (corrections, playbooks, insights, patterns) from this session into the compound-learnings store so future sessions start smarter. Project-scoped by default; global promotion is opt-in.
allowed-tools: Bash(python3:*), Bash(mkdir:*), Bash(rm:*), Bash(git add:*), Bash(git commit:*), Bash(git status:*), Read, Write, Edit, Glob, Grep
---

# Compound Learnings — Capture

Capture durable work-lessons and file them into the learnings store for retrieval
in future sessions. Learnings are the agent's own lessons — **not** source-document
wiki pages (use `/wiki-compile` for those) and **not** user preferences/behaviors
(those go to MEMORY).

The store is two-tier: the project store `.compound/` (primary, committed) and
the opt-in global store `~/.claude/compound-knowledge/` (cross-project). Read
`templates/learning-schema.md` for the full contract before writing.

**Announce at start:** "Using learn-capture to capture session learnings into `.compound/`."

Modes (from `$ARGUMENTS`):
- *(no args)* — **capture now** from the current session.
- `--review` — review pending drafts in `.drafts/` and approve/edit/discard.
- `--audit` — staleness/dedup sweep over the store (see Step A).

---

## Capture (default)

### Step 1: Identify candidates

Scan the session for **1–3** compoundable lessons (quality over quantity). For each,
classify a `type`:

| type | signal |
|------|--------|
| correction | a mistake made / "don't do that" / a fix that reversed an earlier choice |
| playbook | a repeatable sequence the user blessed ("that worked") |
| insight | new understanding of a problem or domain |
| pattern | a recurring behavior/structure worth noting |

**Redirect, don't file:** if a candidate is really a user *preference* or *behavior*
("the user prefers X"), do **not** file it as a learning — save it to MEMORY instead.

### Step 2: Draft + classify scope

For each candidate, draft a one-sentence headline (≤100 chars) plus Learning / Context /
Implication. **Default `scope: project`.** Propose `scope: global` **only** if the lesson
clearly generalizes beyond this repo (a language/tool/process truth, not a fact about this
codebase). Global is a separate, explicit choice — never the default.

Present the drafts to the user. **Never save without approval.**

### Step 3: Check for conflicts (dedup-on-write)

For each approved learning, classify it against the existing store with the resolver —
this returns **CREATE / UPDATE / SKIP / SUPERSEDE** (dry-run; no writes):

```bash
python3 tools/resolve_learnings.py .compound/.drafts/<id>.md --root .compound
```

Act on the resolution:
- **CREATE** → proceed to Step 4 (new learning).
- **SKIP** → an identical learning already exists; don't file a duplicate.
- **UPDATE** → refine the existing learning in place instead of creating a near-dup:
  `python3 -c "from lib.learning_store import edit_learning; ..."` then re-`append` its line.
- **SUPERSEDE** → a new **correction contradicts** an active learning ("corrections always
  win"). With user approval, re-run with `--apply` to stamp the old entry
  `status: superseded`, archive it, and drop it from the index — then file the new
  correction in Step 4:

  ```bash
  python3 tools/resolve_learnings.py .compound/.drafts/<id>.md --root .compound --apply
  ```

The resolver keys on the learning's **topic slug**, so the same lesson recaptured later
resolves against the original rather than piling up duplicates.

### Step 4: Write + index (validated, single index owner)

For each approved learning:

1. Fill `templates/learning-template.md` with the content, the derived `id`, and today's date.
2. Stage it as a draft, then validate-write-index in one gated step:

```bash
mkdir -p .compound/.drafts
# (Write the learning markdown to .compound/.drafts/<id>.md via the Write tool)
python3 tools/learning_write.py .compound/.drafts/<id>.md --root .compound
```

`learning_write.py` validates first — **invalid content never reaches disk** — then writes
to `.compound/<type-dir>/<id>.md` and appends exactly one line to `.compound/index.md`.
Do **not** hand-edit `index.md`; that tool is its sole owner.

3. For a **global**-scoped learning, run the same with `--root "$HOME/.claude/compound-knowledge"`
   (the store self-creates; `git init` it once if new).
4. Remove the draft and stage the result:

```bash
rm .compound/.drafts/<id>.md
git add .compound
git commit -m "[learn-capture] Filed: <headline>"
```

### Step 5: Confirm

Report what was filed (id, type, scope, path) and that it will surface automatically when
relevant in future sessions.

---

## `--review`

List `.compound/.drafts/*.md` (and the global drafts dir). Two kinds of draft live here:
- **Manual** drafts you staged in Step 4.
- **Auto-detected stubs** (`auto-<ts>-<type>.md`) staged by the `learn-capture` Stop hook when
  it spotted a compoundable moment. These are skeletons — an empty headline/body plus a
  `<!-- AUTO-DETECTED … -->` note recording the signal. They are **not** saved learnings.

For each draft, show the headline (or the detected signal, for stubs) and type. For a stub,
**synthesize a real headline + Learning/Context/Implication** from the session it flagged.
Then let the user approve (→ Step 3 conflict check → Step 4), edit, or discard (`rm`). Drafts
are excluded from the index, so an un-reviewed draft costs zero retrieval tokens.

---

## Step A: `--audit`

A conservative staleness + conflict sweep. **Archive, never delete.**

1. **Rebuild the index** so it reflects the store on disk (drops anything already archived):

   ```bash
   python3 tools/learning_index.py rebuild --root .compound
   ```

2. **Flag stale entries.** From the index, list learnings that are both **old** and
   **low-confidence** (`UNCERTAIN`, or `INFERRED` past its usefulness). Present them; let the
   user confirm archive (move the file under `.archive/` and `rebuild`) or keep.

3. **Resolve contradictions ("corrections always win").** For each active **correction**,
   classify it against the rest of the store to surface any active non-correction it
   contradicts on the same topic:

   ```bash
   python3 tools/resolve_learnings.py .compound/corrections/<id>.md --root .compound
   ```

   On a `SUPERSEDE` verdict, with user approval re-run with `--apply` to archive the
   contradicted learning + rebuild. Be conservative — confirm before applying.

4. **Report.** Summarize what was rebuilt, flagged, archived, or left untouched. Never
   bulk-delete; archival keeps the active index small without losing the audit trail.

---

## Guardrails

- **Approval required** — never auto-save; never silent-write.
- **1–3 learnings max** per capture.
- **Project scope by default**; global promotion is explicit and rare.
- **Preferences/behaviors → MEMORY**, not the learnings store.
- **Validate before writing** — always go through `tools/learning_write.py`.
- **`index.md` has one owner** — `tools/learning_index.py` (via `learning_write.py`). Never hand-edit it.
