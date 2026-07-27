<p align="center">
  <img src="loomgit/web/logo.png" width="120" height="120" alt="loomgit logo" style="border-radius: 16px;">
</p>

<h1 align="center">loomgit</h1>

<p align="center">
  <strong>The AI-Powered Developer Memory & Context Engine</strong>
</p>

<p align="center">
  <a href="#-architecture--how-it-works"><img src="https://img.shields.io/badge/Architecture-Hybrid%20Vector%20%2B%20SQL-blueviolet?style=flat-square" alt="Architecture"></a>
  <a href="#-benchmark--feature-comparison"><img src="https://img.shields.io/badge/LLM-Groq%20Llama%203.3%2070B-emerald?style=flat-square" alt="LLM Engine"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="License"></a>
  <a href="#-mcp-integration-setup-antigravity--claude"><img src="https://img.shields.io/badge/Protocol-MCP%20Server-orange?style=flat-square" alt="MCP Protocol"></a>
</p>

<p align="center">
  <code>loomgit</code> automatically captures, structures, and semantically indexes your coding decisions, bug fixes, architecture choices, and lessons learned into an AI-queryable memory graph.
</p>

---

## 🚀 Step-by-Step Setup Guide (From Scratch)

Follow these quick commands to set up `loomgit`, enable Git auto-capturing, and connect your AI coding assistants in under 2 minutes.

### 1️⃣ Installation

```bash
git clone https://github.com/Mohamedarsath26/devmemory.git
cd devmemory
pip install -e .
```

### 2️⃣ Configure API Keys

Set up your Groq (Llama 3.3 70B) and Google Gemini (Embeddings) keys:

```bash
loomgit setup
```

---

### 3️⃣ Enable Auto-Git Capture (Git Hook)

Install the automatic `post-commit` hook in any Git repository so `loomgit` captures every commit automatically:

```bash
# Run inside your project repository:
loomgit install-hook
```

> **How it works:** Once installed, `loomgit` automatically triggers on **every commit**, whether made via:
> - 💻 **Terminal / CLI:** Manual `git commit -m "..."`
> - 🎨 **VS Code / IDE GUI:** Commit button in Source Control UI, Cursor, or JetBrains IDEs
>
> It extracts your code diff, runs smart per-file chunking through Groq LLM, and indexes your intent automatically in the background.

---

### 4️⃣ Connect to AI Coding Assistants (MCP Setup)

`loomgit` provides 1-command automated setup for AI pair programmers:

#### 🌌 Option A: Connect to Google DeepMind Antigravity IDE
```bash
loomgit setup-antigravity
```
*Configures Antigravity's MCP server configuration automatically.*

#### 🤖 Option B: Connect to Claude Code / Claude Desktop
```bash
loomgit setup-claude
```
*Configures `claude_desktop_config.json` automatically.*

---

## 💻 CLI Commands & Usage

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
| **Standalone Local Web Dashboard** | 📊 **Yes (Kamino UI)** | ❌ No | ❌ SaaS / Cloud | ❌ No | ⚠️ Static HTML report |
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

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.
