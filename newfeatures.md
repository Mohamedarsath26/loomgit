# Proposed Next Features for `devmemory`

This document outlines the roadmap for future enhancements to the `devmemory` project.

---

## 1. Automated Git Hook Integration 🐙
- **Goal**: Automatically intercept `git commit` messages and store them as memories without manual CLI input.
- **How it works**:
  - Implement `capture/git.py` to extract commit hash, commit message, author, and changed files.
  - Provide a command `mem install-hook` that installs a `post-commit` script into `.git/hooks/`.
  - Every time you run `git commit -m "..."`, the hook fires `devmemory` in the background with `source="git"`.

---

## 2. Google Agent Development Kit (ADK) Tool 🤖
- **Goal**: Expose `devmemory` as a standard Agent Tool for AI coding assistants (Google ADK, LangChain, LlamaIndex, or Claude Agent).
- **How it works**:
  - Create `devmemory/agent_tools.py`.
  - Wrap `memory.search()` and `memory.capture()` as tool functions complete with docstrings and type annotations.
  - Enable AI agents to query developer memories during pair programming sessions automatically.

---

## 3. Rich Terminal UI 🎨
- **Goal**: Upgrade CLI output using the `rich` library for a sleek, modern developer UX.
- **How it works**:
  - Add `rich` to dependencies.
  - Format `mem search` output into styled cards with colored badges for `MemoryType` (`BUG_FIX`, `DECISION`, `ARCHITECTURE`), highlighted code paths, and formatted tags.
  - Add progress spinners during AI extraction and embedding steps.

---

## 4. Local Web Dashboard 🌐
- **Goal**: A visual web interface to browse, filter, search, and manage all developer memories.
- **How it works**:
  - Build a lightweight backend using FastAPI.
  - Create a modern single-page dashboard (HTML + Tailwind CSS / JavaScript).
  - Include interactive features: search bar with live semantic results, filter by memory type/tag, and view detailed memory timelines.
