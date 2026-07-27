import argparse
from pathlib import Path
from loomgit import Memory
import shutil
import sys
import io
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import json

# Force UTF-8 output to avoid Windows cp1252 encoding errors with unicode symbols
if sys.platform == "win32" and not isinstance(sys.stdout, io.TextIOWrapper):
    console = Console()
else:
    console = Console(file=open(sys.stdout.fileno(), mode='w', encoding='utf-8', closefd=False))

from rich.box import ROUNDED
from rich.rule import Rule
from rich.theme import Theme

from loomgit.config import load_config, save_config, CONFIG_FILE


# Claude Code inspired color palette and theme
TYPE_STYLES = {
    "bug_fix": ("bold white on red", "red"),
    "decision": ("bold white on cyan", "cyan"),
    "architecture": ("bold white on magenta", "magenta"),
    "tool_usage": ("bold black on green", "green"),
    "lesson_learned": ("bold black on yellow", "yellow"),
    "note": ("bold white on blue", "blue"),
    "migration": ("bold white on dark_orange", "dark_orange"),
    "experiment": ("bold white on purple", "purple"),
    "api_failure": ("bold white on bright_red", "bright_red"),
}

def main():
    parser = argparse.ArgumentParser(description="loomgit CLI - Developer AI Context Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    log_parser = subparsers.add_parser("log", help="Log a manual memory")
    log_parser.add_argument("message", type=str, help="The text you want to remember")

    search_parser = subparsers.add_parser("search", help="Search your memories")
    search_parser.add_argument("query", type=str, help="What you want to search for")

    list_parser = subparsers.add_parser("list", help="List all memories chronologically (date & time wise)")
    list_parser.add_argument("--limit", type=int, default=20, help="Number of records to show (default: 20)")
    list_parser.add_argument("--asc", action="store_true", help="Show oldest first (default: newest first)")

    subparsers.add_parser("install-hook", help="Install post-commit Git hook")
    subparsers.add_parser("log-git", help="Capture the latest Git commit into loomgit")

    subparsers.add_parser("setup", help="Configure API keys for loomgit")

    subparsers.add_parser("setup-antigravity", help="Connect loomgit MCP to Antigravity IDE")
   
    subparsers.add_parser("setup-claude", help="Connect loomgit MCP to Claude Code")

    ui_parser = subparsers.add_parser("ui", help="Launch local web dashboard in browser")
    ui_parser.add_argument("--port", type=int, default=8000, help="Port to run the dashboard server (default: 8000)")
    ui_parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default: 127.0.0.1)")

    dashboard_parser = subparsers.add_parser("dashboard", help="Launch local web dashboard in browser")
    dashboard_parser.add_argument("--port", type=int, default=8000, help="Port to run the dashboard server (default: 8000)")
    dashboard_parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default: 127.0.0.1)")

    args = parser.parse_args()

    db_dir = Path.home() / ".loomgit"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / "store.db"

    legacy_db_path = Path.home() / ".devloom" / "store.db"
    if legacy_db_path.exists():
        try:
            if not db_path.exists() or db_path.stat().st_size < 30000:
                shutil.copy2(legacy_db_path, db_path)
            legacy_qdrant = Path.home() / ".devloom" / "qdrant_db"
            qdrant_dir = db_dir / "qdrant_db"
            if legacy_qdrant.exists() and not qdrant_dir.exists():
                shutil.copytree(legacy_qdrant, qdrant_dir)
        except Exception:
            pass
    
    if args.command == "log":
        with console.status("[bold cyan]Processing memory with AI...[/bold cyan]", spinner="dots"):
            memory = Memory(db_path=db_path)
            memory.capture(source="manual", raw_text=args.message)
        console.print("\n[bold green]✓[/bold green] [bold]Successfully logged memory to loomgit![/bold]\n")
        
    elif args.command == "search":
        console.print(Rule("[bold magenta]🧠 loomgit[/bold magenta]", style="dim"))
        
        with console.status(f"[bold cyan]Searching memories for:[/bold cyan] [italic]'{args.query}'[/italic]...", spinner="dots"):
            memory = Memory(db_path=db_path)
            results = memory.search(args.query)

        if not results:
            console.print(f"\n[yellow]No memories found matching:[/yellow] [italic]'{args.query}'[/italic]\n")
            return
            
        console.print(f"\n[dim]Found {len(results)} relevant memory record(s):[/dim]\n")

        for record in results:
            badge_style, border_color = TYPE_STYLES.get(record.type.value, ("bold white on blue", "blue"))
            date_str = record.timestamp.strftime('%b %d, %Y • %I:%M %p')

            # Header badge for top border
            title_text = f"[{badge_style}] {record.type.value.upper()} [/{badge_style}]"

            body_lines = [
                f"[bold white]{record.summary}[/bold white]",
                f"[dim]🕒 {date_str}[/dim]"
            ]

            if record.what_changed:
                body_lines.append(f"\n[bold cyan]🔧 What changed:[/bold cyan]\n  {record.what_changed}")
                
            if record.related_files:
                files_str = " ".join([f"[reverse cyan] {f} [/reverse cyan]" for f in record.related_files])
                body_lines.append(f"\n[bold yellow]📁 Files:[/bold yellow] {files_str}")
                
            if record.tags:
                tags_str = " ".join([f"[bold black on bright_black] #{t} [/bold black on bright_black]" for t in record.tags])
                body_lines.append(f"\n[bold green]🏷️  Tags:[/bold green] {tags_str}")

            body_lines.append(f"\n[bold magenta]💡 Reasoning:[/bold magenta]\n  [italic]{record.reasoning}[/italic]")

            body_content = "\n".join(body_lines)

            console.print(Panel(
                body_content,
                title=title_text,
                title_align="left",
                border_style=border_color,
                box=ROUNDED,
                padding=(1, 2)
            ))
            console.print()

    elif args.command == "list":
        console.print(Rule("[bold magenta]🧠 loomgit timeline[/bold magenta]", style="dim"))
        order = "ASC" if args.asc else "DESC"
        with console.status("[bold cyan]Fetching memory timeline...[/bold cyan]", spinner="dots"):
            memory = Memory(db_path=db_path)
            results = memory.list_all(limit=args.limit, order=order)

        if not results:
            console.print("\n[yellow]No memories stored yet![/yellow]\n")
            return

        order_label = "oldest first" if args.asc else "newest first"
        console.print(f"\n[dim]Showing {len(results)} memory record(s) ({order_label}):[/dim]\n")

        for record in results:
            badge_style, border_color = TYPE_STYLES.get(record.type.value, ("bold white on blue", "blue"))
            date_str = record.timestamp.strftime('%b %d, %Y • %I:%M:%S %p')

            title_text = f"[{badge_style}] {record.type.value.upper()} [/{badge_style}]"

            body_lines = [
                f"[bold white]{record.summary}[/bold white]",
                f"[dim]🕒 {date_str}[/dim]"
            ]

            if record.what_changed:
                body_lines.append(f"\n[bold cyan]🔧 What changed:[/bold cyan]\n  {record.what_changed}")
                
            if record.related_files:
                files_str = " ".join([f"[reverse cyan] {f} [/reverse cyan]" for f in record.related_files])
                body_lines.append(f"\n[bold yellow]📁 Files:[/bold yellow] {files_str}")
                
            if record.tags:
                tags_str = " ".join([f"[bold black on bright_black] #{t} [/bold black on bright_black]" for t in record.tags])
                body_lines.append(f"\n[bold green]🏷️  Tags:[/bold green] {tags_str}")

            body_lines.append(f"\n[bold magenta]💡 Reasoning:[/bold magenta]\n  [italic]{record.reasoning}[/italic]")

            body_content = "\n".join(body_lines)

            console.print(Panel(
                body_content,
                title=title_text,
                title_align="left",
                border_style=border_color,
                box=ROUNDED,
                padding=(1, 2)
            ))
            console.print()

    elif args.command == "install-hook":
        git_dir = Path.cwd() / ".git"
        if not git_dir.exists():
            console.print("[bold red]✗ Error:[/bold red] Not a git repository! Run this command inside a git repository.")
            return

        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        hook_path = hooks_dir / "post-commit"

        loomgit_path = shutil.which("loomgit")
        if loomgit_path:
            bash_path = loomgit_path.replace("\\", "/").replace("C:/", "/c/")
        else:
            bash_path = "loomgit"

        hook_script = f"#!/bin/sh\n\"{bash_path}\" log-git > /dev/null 2>&1 &\n"
        hook_path.write_text(hook_script, encoding="utf-8")

        try:
            hook_path.chmod(0o755)
        except Exception:
            pass

        console.print(f"\n[bold green]✓[/bold green] Installed Git post-commit hook into [cyan]{hook_path}[/cyan]\n")

    elif args.command == "log-git":
        with console.status("[bold cyan]Extracting & embedding Git commit...[/bold cyan]", spinner="dots"):
            memory = Memory(db_path=db_path)
            captured = memory.capture(source="git")
        if captured:
            console.print("\n[bold green]✓[/bold green] [bold]Captured Git commit memory![/bold]\n")
        else:
            console.print("\n[bold yellow]ℹ[/bold yellow] [bold]Commit was already captured in loomgit. Skipped duplicate.[/bold]\n")

    elif args.command == "setup":
        console.print("\n[bold cyan]🧠 Welcome to loomgit setup![/bold cyan]\n")

        config = load_config()

        groq_key = input("🔑 Enter your Groq API key: ").strip()
        google_key = input("🔑 Enter your Google API key: ").strip()

        config["groq_api_key"] = groq_key
        config["google_api_key"] = google_key

        save_config(config)

        console.print(f"\n[bold green]✓[/bold green] API keys saved to [cyan]{CONFIG_FILE}[/cyan]")
        console.print("[bold green]✓[/bold green] You're all set! Try: [cyan]loomgit log \"my first memory\"[/cyan]\n")

    elif args.command == "setup-antigravity":
        console.print("\n[bold cyan]>> Connecting loomgit to Antigravity...[/bold cyan]\n")

        config = load_config()
        if not config.get("groq_api_key") or not config.get("google_api_key"):
            console.print("[bold red]✗[/bold red] API keys not found! Run [cyan]loomgit setup[/cyan] first.\n")
            return
        mcp_config_path = Path.home() / ".gemini" / "antigravity-ide" / "mcp_config.json"
        if not mcp_config_path.exists():
            console.print(f"[bold red]✗[/bold red] Antigravity config not found at [cyan]{mcp_config_path}[/cyan]")
            console.print("[dim]Make sure Antigravity IDE is installed.[/dim]\n")
            return
        
        try:
            mcp_data = json.load(open(mcp_config_path, "r"))
        except json.JSONDecodeError:
            mcp_data = {"mcpServers": {}}

        python_path = shutil.which("python") or "python"

        mcp_data["mcpServers"]["loomgit"] = {
            "command": python_path,
            "args": ["-m", "loomgit.mcp_server"],
            "env": {
                "GROQ_API_KEY": config["groq_api_key"],
                "GOOGLE_API_KEY": config["google_api_key"],
            }
        }

        with open(mcp_config_path, "w") as f:
            json.dump(mcp_data, f, indent=2)

        console.print(f"[bold green]✓[/bold green] Added loomgit MCP server to [cyan]{mcp_config_path}[/cyan]")
        console.print("[bold green]✓[/bold green] Restart Antigravity to activate! 🚀\n")

    elif args.command == "setup-claude":
        console.print("\n[bold cyan]>> Connecting loomgit to Claude Code...[/bold cyan]\n")

        config = load_config()
        if not config.get("groq_api_key") or not config.get("google_api_key"):
            console.print("[bold red]✗[/bold red] API keys not found! Run [cyan]loomgit setup[/cyan] first.\n")
            return

        claude_config_path = Path.home() / ".claude.json"

        try:
            claude_data = json.load(open(claude_config_path, "r"))
        except (FileNotFoundError, json.JSONDecodeError):
            claude_data = {"mcpServers": {}}

        python_path = shutil.which("python") or "python"

        claude_data.setdefault("mcpServers", {})
        claude_data["mcpServers"]["loomgit"] = {
            "command": python_path,
            "args": ["-m", "loomgit.mcp_server"],
            "env": {
                "GROQ_API_KEY": config["groq_api_key"],
                "GOOGLE_API_KEY": config["google_api_key"],
            }
        }

        with open(claude_config_path, "w") as f:
            json.dump(claude_data, f, indent=2)

        console.print(f"[bold green]✓[/bold green] Connected [cyan]loomgit[/cyan] MCP server to [bold]Claude Code[/bold] at [cyan]{claude_config_path}[/cyan]\n")

    elif args.command in ["ui", "dashboard"]:
        import uvicorn
        import webbrowser
        import threading

        port = args.port
        host = args.host
        url = f"http://{host}:{port}"

        console.print(f"\n[bold cyan]🧠 Starting loomgit Local Web Dashboard...[/bold cyan]")
        console.print(f"[bold green]✓[/bold green] Server running at [bold underline cyan]{url}[/bold underline cyan]\n")

        def open_browser():
            try:
                webbrowser.open(url)
            except Exception:
                pass

        threading.Timer(1.0, open_browser).start()
        uvicorn.run("loomgit.web.app:app", host=host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
