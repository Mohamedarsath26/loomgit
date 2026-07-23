# SKILL: Build "devmemory" — AI Memory for Developers

## What this document is

This is a complete build spec for **devmemory**, a personal "second brain" that
captures why developers make decisions (architecture choices, bug fixes,
migrations, prompt experiments, API failures) and lets them query that history
months later in natural language. This doc is meant to be handed to an
agentic coding tool (Antigravity, Claude Code, Cursor, Gemini CLI) as the
single source of truth for the build. It should not need external
clarification to start implementation — where a decision is ambiguous,
a default is stated explicitly.

Read this entire document before writing code. Build in the phase order
given in "Build Plan" — do not skip ahead to MCP integration before the
core library works standalone.

---

## 1. Product summary

**One-line pitch:** A tool that watches your dev workflow (commits, chat
sessions, migrations, bug fixes) and lets you ask "why did I do X?" six
months later and get a synthesized, cited answer.

**Core user loop:**
1. Something happens (commit, manual note, failed CI run, AI chat session).
2. devmemory captures the raw event.
3. An LLM extraction step turns it into a structured memory record.
4. The record is embedded and stored (vector + structured DB).
5. Later, the user asks a question via CLI, library call, or MCP tool call
   from an editor/agent.
6. devmemory retrieves relevant memories and synthesizes a cited answer.

**Non-goals (explicitly out of scope for v1):**
- No team/multi-user sync — local-first, single developer.
- No real-time "watching" via OS-level file monitoring — capture is
  event-triggered (git hooks, explicit CLI calls, webhook receivers), not
  a background daemon that reads arbitrary files.
- No web UI in v1 — CLI + library + MCP server only.
- No automatic PII/secrets redaction in v1 — flag as a known limitation in
  the README; do not attempt to build a redaction pipeline this pass.

---

## 2. Architecture overview

Three layers, each independently testable:

```
CAPTURE  →  EXTRACT  →  STORE  →  RETRIEVE
(events)    (LLM)       (hybrid)   (RAG + synth)
```

Three interfaces sit on top of the same core library — none of them contain
business logic, they are thin adapters:

```
┌─────────────┐  ┌─────────────┐  ┌──────────────┐
│   CLI        │  │  Library     │  │  MCP Server   │
│  (mem ask)   │  │ (import as   │  │ (tools for    │
│              │  │  package)    │  │  editors)     │
└──────┬───────┘  └──────┬───────┘  └──────┬────────┘
       └─────────────────┼──────────────────┘
                          ▼
              ┌───────────────────────┐
              │   devmemory core       │
              │  capture/extract/store │
              │  /query modules        │
              └───────────────────────┘
```

**Golden rule:** the MCP server, CLI, and any future web UI must all call
the same core functions (`capture_event()`, `query()`). Never duplicate
extraction or retrieval logic in an adapter.

---

## 3. Tech stack (defaults — deviate only if there's a strong reason)

- **Language:** Python 3.11+
- **Package manager:** `uv` or `pip` with `pyproject.toml`
- **Structured store:** SQLite (via `sqlite3` stdlib or `sqlmodel`) — zero
  setup, file-based, matches "local-first library" positioning.
- **Vector store:** `sqlite-vec` extension (keeps everything in one file) as
  the default. Design the store behind an interface (`VectorStore`
  abstract base) so Qdrant/LanceDB can be swapped in later — but ship v1
  with sqlite-vec only. Do not build multiple backends in v1.
- **Embeddings:** pluggable via a single `Embedder` interface. Default to
  a local/small embedding model to keep the tool usable offline
  (e.g. via `sentence-transformers`); allow an API-based embedder
  (OpenAI/Voyage/Anthropic) as a config option.
- **LLM for extraction & synthesis:** pluggable via an `LLMClient`
  interface. Default to Anthropic API (`claude-sonnet-4-6`) since this is
  the primary target ecosystem (Claude Code/MCP), but keep it swappable.
- **CLI framework:** `typer` or `click`.
- **MCP server:** official `mcp` Python SDK, stdio transport by default.
- **Config:** single `~/.devmemory/config.toml` — store paths, model
  choices, API key env var names (never store raw keys in config).

---

## 4. Data model

### 4.1 Raw event (capture layer output)

```python
class RawEvent(BaseModel):
    id: str                # uuid
    source: Literal["git", "manual", "chatlog", "ci", "webhook"]
    raw_text: str           # commit msg + diff, note text, stack trace, etc.
    metadata: dict          # source-specific: {"commit_sha": "...", "files": [...]}
    timestamp: datetime
    processed: bool = False # extraction pipeline sets True once handled
```

Raw events are stored **verbatim and permanently**, even after extraction.
Extraction quality will improve over time; you must be able to re-run
extraction against raw events without recapturing.

### 4.2 Memory record (extraction layer output)

```python
class MemoryType(str, Enum):
    DECISION = "decision"
    BUG_FIX = "bug_fix"
    MIGRATION = "migration"
    EXPERIMENT = "experiment"
    API_FAILURE = "api_failure"
    NOTE = "note"           # fallback when classification is unclear

class MemoryRecord(BaseModel):
    id: str
    raw_event_id: str        # FK to RawEvent
    type: MemoryType
    summary: str              # one-line, <120 chars
    reasoning: str             # the "why" — this is what gets embedded
    tags: list[str]
    related_files: list[str]
    source_ref: str            # e.g. "commit:a3f9c21", "note:manual"
    timestamp: datetime
    embedding: list[float] | None  # populated after embedding step
```

**Important:** embed `summary + reasoning` concatenated, not the raw event.
Raw commit diffs are noisy; the distilled reasoning is what makes semantic
search actually useful for "why did I do X" queries.

### 4.3 SQLite schema

```sql
CREATE TABLE raw_events (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    metadata TEXT NOT NULL,       -- JSON blob
    timestamp TEXT NOT NULL,
    processed INTEGER DEFAULT 0
);

CREATE TABLE memory_records (
    id TEXT PRIMARY KEY,
    raw_event_id TEXT NOT NULL REFERENCES raw_events(id),
    type TEXT NOT NULL,
    summary TEXT NOT NULL,
    reasoning TEXT NOT NULL,
    tags TEXT NOT NULL,            -- JSON array
    related_files TEXT NOT NULL,   -- JSON array
    source_ref TEXT NOT NULL,
    timestamp TEXT NOT NULL
);

-- sqlite-vec virtual table for embeddings
CREATE VIRTUAL TABLE memory_vectors USING vec0(
    memory_id TEXT PRIMARY KEY,
    embedding FLOAT[384]           -- dim depends on embedder model
);

CREATE INDEX idx_memory_type ON memory_records(type);
CREATE INDEX idx_memory_timestamp ON memory_records(timestamp);
```

---

## 5. Capture layer — implementation detail per source

### 5.1 Git hook (`post-commit`)

- Installed via `devmemory init` which writes `.git/hooks/post-commit`
  (or symlinks to a script in the repo so it's shareable via a
  `.devmemory-hooks/` dir committed to the repo).
- Hook script calls: `devmemory capture --source git --ref HEAD`
- Reads commit message via `git log -1 --format=%B HEAD` and diff stat via
  `git show --stat HEAD`. Do NOT embed full diffs for large commits —
  truncate diff content to ~200 lines and rely on the commit message as
  primary signal; note in metadata if truncated.

### 5.2 Manual CLI note

```bash
mem log "switched from ChromaDB to Qdrant because filtering was too slow"
```
- Directly creates a `RawEvent` with `source="manual"`, immediately
  eligible for extraction (no batching needed for single notes).

### 5.3 Chat log importer

- Support importing Claude Code session transcripts (JSON/JSONL export
  format) and generic chat exports (a simple `{role, content}[]` schema
  as the lowest common denominator).
- One `RawEvent` per session (not per message) — concatenate the
  conversation, cap at a reasonable token budget (~8k tokens), and let
  extraction pull out the decision-relevant parts.
- CLI: `devmemory import --source chatlog --file session.json`

### 5.4 CI/test failure hook

- Accepts a webhook POST (simple local HTTP receiver, `devmemory serve
  --port 8420`) or a CLI call from within a CI script:
  `devmemory capture --source ci --text "$(cat failure.log)"`.

### 5.5 Migration files

- Watch a configured migrations directory pattern (e.g. `migrations/*.sql`,
  `alembic/versions/*.py`) — triggered manually via
  `devmemory capture --source migration --file <path>`, or automatically
  from the git hook when a commit touches a path matching the configured
  migration glob.

**Do not build a filesystem-watching daemon in v1.** All capture is
triggered by an explicit event (git hook, CLI invocation, webhook POST).
This keeps the "watching" framing honest without the complexity/privacy
cost of a background process reading arbitrary files.

---

## 6. Extraction layer

### 6.1 Extraction prompt (system prompt template)

The extraction step is a single LLM call per raw event. Use structured
output (JSON mode / tool use) so parsing is reliable.

```
You are extracting a structured memory record from a developer's raw
activity log. Given the raw text and metadata below, produce a JSON object
with these fields:

- type: one of "decision", "bug_fix", "migration", "experiment",
  "api_failure", "note". Use "note" only if none of the others fit.
- summary: one sentence, under 120 characters, plain description of what
  happened.
- reasoning: 1-4 sentences capturing WHY this happened — the actual
  reasoning, trade-offs, or root cause. This is the most important field.
  If the raw text contains no reasoning (e.g. a terse commit message),
  say so explicitly rather than inventing a rationale.
- tags: 3-6 lowercase, hyphenated tags (technology names, concepts).
- related_files: file paths mentioned or changed, if any.

Respond with ONLY the JSON object, no preamble, no markdown fences.

Raw event source: {source}
Raw text:
{raw_text}

Metadata:
{metadata}
```

### 6.2 Extraction rules

- **Never fabricate reasoning.** If a commit message is just "fix bug" with
  no context, the extracted `reasoning` should say something like "No
  explicit reasoning given in source; see diff for context" rather than
  guessing. This matters a lot for trustworthiness of later answers.
- Extraction should be **idempotent and re-runnable**: store `raw_event_id`
  on every `MemoryRecord`, and support `devmemory reprocess --all` to
  re-extract everything against an improved prompt/model later.
- Batch extraction for chat log imports (one call per session, not per
  message) to control cost.
- After extraction, immediately embed `summary + " " + reasoning` and
  write to the vector table in the same transaction as the memory record
  insert (avoid orphaned records with no embedding).

---

## 7. Retrieval & synthesis layer

### 7.1 Query flow

```python
def query(question: str, filters: QueryFilters | None = None) -> Answer:
    query_embedding = embedder.embed(question)
    candidates = vector_store.search(query_embedding, top_k=10, filters=filters)
    # candidates: list[MemoryRecord] ranked by cosine similarity
    answer_text = llm.synthesize(question, candidates)
    return Answer(text=answer_text, sources=[c.source_ref for c in candidates[:5]])
```

- `top_k=10` retrieved, but only pass the top 5 most relevant into the
  synthesis prompt to keep context tight and citations meaningful.
- Support metadata filters (`type=`, `tag=`, date range) as optional CLI
  flags: `mem ask "..." --type decision --since 2026-01-01`.

### 7.2 Synthesis prompt template

```
Answer the developer's question using ONLY the memory records provided
below. Cite which record(s) support each claim using their source_ref.
If the memories don't fully answer the question, say what's missing
rather than guessing.

Question: {question}

Memory records:
{formatted_candidates}

Respond in plain text (not JSON): a direct answer, followed by a
"Sources:" list of source_refs used.
```

### 7.3 Related-memory expansion (the "pulled in the migration too" behavior)

After retrieving top candidates by semantic similarity, run a secondary
lookup: for each candidate's `timestamp`, pull any other memory records
within a ±3 day window that share at least one tag. Include these as
"related context" in the synthesis prompt, clearly separated from the
primary hits, so the model can mention them without treating them as
equally central to the answer.

---

## 8. Interfaces

### 8.1 Library API (the core — everything else wraps this)

```python
import devmemory

memory = devmemory.Memory(db_path="~/.devmemory/store.db")

memory.capture(source="manual", raw_text="...", metadata={})
memory.capture_git_commit(ref="HEAD")
memory.import_chatlog(path="session.json")

answer = memory.query("why did I switch from ChromaDB to Qdrant?")
print(answer.text)
print(answer.sources)
```

### 8.2 CLI

```bash
devmemory init                          # installs git hook, creates config
mem log "<note text>"                   # manual capture, alias for capture --source manual
devmemory capture --source git --ref HEAD
devmemory import --source chatlog --file session.json
mem ask "<question>" [--type X] [--since DATE]
devmemory reprocess --all               # re-run extraction on all raw events
devmemory serve --port 8420             # local webhook receiver for CI hooks
```

### 8.3 MCP server

Expose exactly two tools to start — resist the urge to expose more surface
area than needed:

```python
@server.tool()
async def capture_memory(text: str, source: str = "manual") -> str:
    """Store a development decision, bug fix, migration note, or
    experiment result so it can be recalled later. Use this whenever
    the user explains a non-obvious reason for a technical choice."""

@server.tool()
async def query_memory(question: str) -> str:
    """Search past development decisions, bug fixes, and migrations.
    Use this before proposing an approach the user may have already
    tried, or when the user asks 'have I done this before' / 'why did
    I...' style questions."""
```

Registration examples for each target editor:

```bash
# Claude Code
claude mcp add devmemory -- python -m devmemory.mcp_server

# Cursor: add to .cursor/mcp.json
{ "mcpServers": { "devmemory": { "command": "python", "args": ["-m", "devmemory.mcp_server"] } } }

# Gemini CLI / Antigravity: shared config at ~/.gemini/config/mcp_config.json
{ "mcpServers": { "devmemory": { "command": "python", "args": ["-m", "devmemory.mcp_server"] } } }
```

---

## 9. Repository structure

```
devmemory/
  pyproject.toml
  README.md
  devmemory/
    __init__.py          # Memory class — the main library entrypoint
    models.py             # RawEvent, MemoryRecord, MemoryType, Answer
    capture/
      __init__.py
      git.py               # post-commit hook logic
      manual.py
      chatlog.py           # Claude Code / generic chat importers
      ci.py                # webhook receiver
    extract/
      __init__.py
      pipeline.py          # extraction orchestration, reprocess support
      prompts.py           # extraction prompt templates
    store/
      __init__.py
      sqlite_store.py      # structured store
      vector_store.py      # VectorStore interface + sqlite-vec impl
    query/
      __init__.py
      retrieval.py          # semantic search + related-memory expansion
      synthesis.py           # answer generation
      prompts.py
    llm/
      __init__.py
      client.py              # LLMClient interface, Anthropic impl
      embedder.py             # Embedder interface
    cli.py                    # typer app
    mcp_server.py              # MCP tool definitions
    config.py                   # ~/.devmemory/config.toml loader
  hooks/
    post-commit                 # installable git hook script
  tests/
    test_capture.py
    test_extraction.py
    test_retrieval.py
    fixtures/
```

---

## 10. Build plan (phase order — build and test each before moving on)

**Phase 1 — Core storage + models**
Implement `models.py`, `sqlite_store.py`, schema migrations. Write tests
that insert/read raw events and memory records with no LLM involved.

**Phase 2 — Capture (manual only)**
Implement `capture/manual.py` and the `Memory.capture()` method. Get
`mem log "..."` working end-to-end into the raw_events table, no
extraction yet.

**Phase 3 — Extraction pipeline**
Implement `extract/pipeline.py` with the prompt from Section 6. Wire it so
every captured raw event gets processed into a `MemoryRecord`. Test with
real commit messages of varying quality (terse vs detailed) to validate
the "don't fabricate reasoning" rule.

**Phase 4 — Embeddings + vector store**
Implement `vector_store.py` with sqlite-vec. Embed on extraction. Test
that semantic search returns sensible neighbors for a small hand-built
set of records.

**Phase 5 — Retrieval + synthesis**
Implement `retrieval.py` and `synthesis.py`. Get `memory.query()` working
end to end with citations. This is the core "wow" moment — test it
thoroughly with the ChromaDB→Qdrant style example from this spec.

**Phase 6 — CLI**
Wrap everything in `cli.py`. `devmemory init`, `mem log`, `mem ask`.

**Phase 7 — Git hook capture**
Add `capture/git.py` and the installable hook script. Validate the full
loop: commit → hook fires → extraction → queryable within seconds.

**Phase 8 — Chat log import**
Add `capture/chatlog.py`. Start with Claude Code's session export format.

**Phase 9 — MCP server**
Add `mcp_server.py` exposing `capture_memory` / `query_memory`. Register
with Claude Code locally and manually verify both tools work from within
a live coding session before considering this phase done.

**Phase 10 — Polish**
CI webhook receiver, `reprocess --all`, config file, README with setup
instructions for each of the four target editors (Claude Code, Cursor,
Gemini CLI, Antigravity).

Do not parallelize phases 1-5 — each depends on the previous being solid,
since extraction quality and retrieval quality are the two things that
determine whether this product is actually useful versus a novelty.

---

## 11. Known limitations to document in the README (not to solve in v1)

- No secrets/PII redaction — users should be aware raw commit diffs and
  chat logs may contain sensitive data and are stored locally in plaintext
  SQLite.
- Single-user, local-first only — no sync across machines in v1.
- Extraction quality depends entirely on the source text; terse commit
  messages will produce thin memory records. Encourage descriptive commit
  messages / manual `mem log` notes for anything non-obvious.
- No automatic background watching — all capture is event-triggered.

---

## 12. Definition of done for v1

- `devmemory init` in a fresh repo installs the hook and creates config.
- Ten realistic sample commits (mix of terse and detailed messages) can be
  captured, extracted, and then a natural-language question about one of
  them returns a correct, cited answer.
- `mem ask` works with no arguments beyond the question.
- The MCP server is registered and functional in at least Claude Code
  (verify the other three per Section 8.3 configs, but Claude Code is the
  must-pass target).
- All Phase 1-9 tests pass.
