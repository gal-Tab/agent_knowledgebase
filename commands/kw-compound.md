---
description: Capture work-lessons (corrections, playbooks, insights, patterns) from this session into the compound-learnings store so future sessions start smarter. Project-scoped by default; global promotion is opt-in.
allowed-tools: Bash(python3:*), Bash(mkdir:*), Bash(rm:*), Bash(git add:*), Bash(git commit:*), Bash(git status:*), Read, Write, Edit, Glob, Grep
---

# Compound Learnings — Capture

Capture durable work-lessons and file them into the learnings store for retrieval
in future sessions. Learnings are the agent's own lessons — **not** source-document
wiki pages (use `/kb-compile` for those) and **not** user preferences/behaviors
(those go to MEMORY).

The store is two-tier: the project store `.compound/` (primary, committed) and
the opt-in global store `~/.claude/compound-knowledge/` (cross-project). Read
`templates/learning-schema.md` for the full contract before writing.

**Announce at start:** "Using kw-compound to capture session learnings into `.compound/`."

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

### Step 3: Check for conflicts (cheap, index-first)

For each approved learning, derive its id and grep the store index(es) for a near-duplicate:

```bash
python3 -c "from lib.learning_store import learning_id; print(learning_id('<headline>', '<today>'))"
grep -i "<key-tag>" .compound/index.md 2>/dev/null
```

- If a clear duplicate exists → offer to **update** the existing learning (edit its body
  via `python3 -c "from lib.learning_store import edit_learning; ..."`) instead of creating a new one.
- If a new **correction contradicts** an active learning → note it; the `--audit` sweep
  (or `tools/resolve_learnings.py`, Phase 3) handles supersession. For now, file the
  correction and flag the conflict to the user.

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
git commit -m "[kw-compound] Filed: <headline>"
```

### Step 5: Confirm

Report what was filed (id, type, scope, path) and that it will surface automatically when
relevant in future sessions.

---

## `--review`

List `.compound/.drafts/*.md` (and the global drafts dir). For each, show the headline and
type; let the user approve (→ Step 4), edit, or discard (`rm`). Drafts are excluded from the
index, so an un-reviewed draft costs zero retrieval tokens.

---

## Step A: `--audit`

Rebuild and sanity-check the store:

```bash
python3 tools/learning_index.py rebuild --root .compound
```

Then scan for stale/conflicting entries (old + low-confidence, or a correction that
contradicts an older learning). Recommend update / merge / archive — be conservative,
prefer archive over delete. (Automated supersession lands in Phase 3 via
`tools/resolve_learnings.py`; "corrections always win".)

---

## Guardrails

- **Approval required** — never auto-save; never silent-write.
- **1–3 learnings max** per capture.
- **Project scope by default**; global promotion is explicit and rare.
- **Preferences/behaviors → MEMORY**, not the learnings store.
- **Validate before writing** — always go through `tools/learning_write.py`.
- **`index.md` has one owner** — `tools/learning_index.py` (via `learning_write.py`). Never hand-edit it.
