<p align="center">
  <img src="https://raw.githubusercontent.com/Mohamedarsath26/devmemory/main/loomgit/web/logo.png" width="120" height="120" alt="loomgit logo" style="border-radius: 16px;">
</p>

<h1 align="center">loomgit</h1>

<p align="center">
  <strong>The AI-Powered Developer Memory & Context Engine</strong>
</p>

<p align="center">
  <a href="#-architecture--how-it-works"><img src="https://img.shields.io/badge/Architecture-Hybrid%20Vector%20%2B%20SQL-blueviolet?style=flat-square" alt="Architecture"></a>
  <a href="#-benchmark--feature-comparison"><img src="https://img.shields.io/badge/LLM-Groq%20Llama%203.3%2070B-emerald?style=flat-square" alt="LLM Engine"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="License"></a>
  <a href="#4%EF%B8%8F%E2%83%93-connect-ai-coding-assistants-mcp-setup"><img src="https://img.shields.io/badge/Protocol-MCP%20Server-orange?style=flat-square" alt="MCP Protocol"></a>
</p>

<p align="center">
  <code>loomgit</code> automatically captures, structures, and semantically indexes your coding decisions, bug fixes, architecture choices, and lessons learned into an AI-queryable memory graph.
</p>

## 📋 Prerequisites

Before installing `loomgit`, make sure you have:
* **Python 3.11+** installed
* **Git** installed and initialized in your project
* **Groq API Key** (Free at [console.groq.com](https://console.groq.com))
* **Google Gemini API Key** (Free at [aistudio.google.com](https://aistudio.google.com))

---

## 🚀 Step-by-Step Getting Started Guide

Follow these sequential steps to set up `loomgit`, configure keys, capture memories, launch the web UI, and connect AI coding assistants.

### 1️⃣ Installation

```bash
git clone https://github.com/Mohamedarsath26/devmemory.git
cd devmemory
pip install -e .
```

---

### 2️⃣ Configure API Keys

Set up your Groq (Llama 3.3 70B) and Google Gemini (Embeddings) keys:

```bash
loomgit setup
```

---

### 3️⃣ Enable Auto-Git Capture (Git Hook)

Install the automatic `post-commit` hook in your repository:

```bash
# Run inside your project repository:
loomgit install-hook
```

> **How it works:** Once installed, `loomgit` automatically triggers on **every commit**, whether made via:
> - 💻 **Terminal / CLI:** Manual `git commit -m "..."`
> - 🎨 **VS Code / IDE GUI:** Commit button in Source Control UI, Cursor, or JetBrains IDEs

---

### 4️⃣ Connect AI Coding Assistants (MCP Setup)

Connect `loomgit` to your AI pair programmer:

#### 🌌 Option A: Connect to Google DeepMind Antigravity IDE
```bash
loomgit setup-antigravity
```

#### 🤖 Option B: Connect to Claude Code / Claude Desktop
```bash
loomgit setup-claude
```

---

### 5️⃣ Launch Local Web Dashboard

Explore your memory timeline, search past decisions, and filter by project scope:

```bash
loomgit ui
```

```text
🧠 Starting loomgit Local Web Dashboard...
✓ Server running at http://127.0.0.1:8001
```

> **View Live Dashboard:** Open **[http://127.0.0.1:8001](http://127.0.0.1:8001)** in your web browser.

<p align="center">
  <img src="https://raw.githubusercontent.com/Mohamedarsath26/devmemory/main/loomgit/web/dashboard_preview.png" width="100%" alt="loomgit Kamino-inspired dark web dashboard preview" style="border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);">
</p>

---

## 💻 CLI Command Reference

| Command | Description | Example |
| :--- | :--- | :--- |
| `loomgit log` | Log a manual memory entry | `loomgit log "Switched to gRPC for speed"` |
| `loomgit search` | Semantic + Keyword search | `loomgit search "gRPC migration"` |
| `loomgit list` | View chronological timeline | `loomgit list --limit 10` |
| `loomgit ui` | Launch local web dashboard | `loomgit ui` |
| `loomgit install-hook` | Enable Git post-commit hook | `loomgit install-hook` |
| `loomgit setup-antigravity` | Auto-connect MCP to Antigravity IDE | `loomgit setup-antigravity` |
| `loomgit setup-claude` | Auto-connect MCP to Claude Code | `loomgit setup-claude` |

---

## ⚖️ Benchmark & Feature Comparison

`loomgit` is designed specifically for **developer memory and codebase intent tracking**. Below is a side-by-side comparison against direct open-source alternatives:

| Feature / Capability | `loomgit` | **aicommits** / **OpenCommit** | **Supermemory** / **Mem0** | **Timescale Memory Engine** | **Graphify** |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Primary Focus** | **Developer Memory & Intent** | Commit message generator | Generic LLM memory | PostgreSQL agent memory | Codebase AST graph |
| **Automatic Git Hook Capture** | ⚡ **Yes (`loomgit install-hook`)** | ⚠️ Manual `git commit` run | ❌ No | ❌ No | ❌ No |
| **AI Intent & Reasoning Analysis** | 🧠 **Llama 3.3 70B** | ❌ Short message only | ⚠️ Generic facts | ⚠️ Unstructured | ❌ Code structure only |
| **Hybrid Search Engine** | 🔍 **Gemini + Qdrant + SQL** | ❌ No search | ⚠️ Vector only | ⚠️ `pgvector` only | ⚠️ Graph traversal |
| **Smart Per-File Diff Budgeting** | 🎯 **Yes (800-char/file)** | ❌ Truncate blob | ❌ No diff parsing | ❌ No diff parsing | ❌ No diff parsing |
| **1-Click MCP Setup (Antigravity/Claude)** | 🔌 **Yes (`setup-antigravity`)** | ❌ No | ⚠️ Partial API | 🔌 Yes | ⚠️ Partial |
| **Standalone Local Web Dashboard** | 📊 **Yes (`loomgit ui`)** | ❌ No | ❌ SaaS / Cloud | ❌ No | ⚠️ Static HTML report |
| **Local-First Zero External DB** | 💻 **SQLite + Local Qdrant** | N/A | ❌ Cloud / External | ❌ Requires Postgres | 💻 Local AST |

---

## 🏛️ Architecture & How It Works

```
                     ┌──────────────────────────────────────────┐
                     │          Developer Activity              │
                     │  (Git Commit / CLI `loomgit log`)       │
                     └────────────────────┬─────────────────────┘
                                          │
                                          ▼
                     ┌──────────────────────────────────────────┐
                     │          Extraction Pipeline             │
                     │  • Per-file Smart Diff Budgeter          │
                     │  • Groq Llama 3.3 70B Engine             │
                     └────────────────────┬─────────────────────┘
                                          │
                        ┌─────────────────┴─────────────────┐
                        ▼                                   ▼
          ┌──────────────────────────┐        ┌──────────────────────────┐
          │  SQLite Store            │        │  Qdrant Vector DB        │
          │  • Chronological Event   │        │  • Google Gemini 768d    │
          │  • SQL LIKE Fallback     │        │    Dense Embeddings      │
          └─────────────┬────────────┘        └─────────────┬────────────┘
                        │                                   │
                        └─────────────────┬─────────────────┘
                                          │
                                          ▼
                     ┌──────────────────────────────────────────┐
                     │          Query & Access Interfaces       │
                     │  • Local Web UI (`loomgit ui`)          │
                     │  • MCP Server (Antigravity / Claude)    │
                     │  • Terminal CLI (`loomgit search`)       │
                     └──────────────────────────────────────────┘
```

---

## 🗺️ Future Roadmap & Planned Features

`loomgit` is actively evolving! Planned upcoming capabilities include:

* **🤖 Multi-LLM Provider Engine:** Support for interchangeable extraction models beyond Groq:
  * **OpenAI** (`gpt-4o`, `gpt-4o-mini`)
  * **Anthropic Claude** (`claude-3-5-sonnet`)
  * **DeepSeek** (`deepseek-chat`, `deepseek-r1`)
  * **Local LLMs** via Ollama / vLLM (100% offline extraction)
* **🔌 Expanded Agentic CLI & MCP Integrations:**
  * **OpenCode / Cursor / Windsurf / Aider / Roo Code** MCP auto-discovery
  * Automated memory recall during pull request reviews
* **🕸️ Graph-Based Relationship Memory:** Temporal knowledge graphs mapping file-to-decision dependencies over time.

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.
