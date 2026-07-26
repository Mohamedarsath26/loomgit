import argparse
from pathlib import Path
from devmemory import Memory
import shutil
import sys
import io
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import shutil
import json

# Force UTF-8 output to avoid Windows cp1252 encoding errors with unicode symbols
if sys.platform == "win32" and not isinstance(sys.stdout, io.TextIOWrapper):
    console = Console()
else:
    console = Console(file=open(sys.stdout.fileno(), mode='w', encoding='utf-8', closefd=False))

from rich.box import ROUNDED
from rich.rule import Rule
from rich.theme import Theme

from devmemory.config import load_config, save_config, CONFIG_FILE


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
    parser = argparse.ArgumentParser(description="devmemory CLI - Developer AI Memory Assistant")
    subparsers = parser.add_subparsers(dest="command", required=True)

    log_parser = subparsers.add_parser("log", help="Log a manual memory")
    log_parser.add_argument("message", type=str, help="The text you want to remember")

    search_parser = subparsers.add_parser("search", help="Search your memories")
    search_parser.add_argument("query", type=str, help="What you want to search for")

    subparsers.add_parser("install-hook", help="Install post-commit Git hook")
    subparsers.add_parser("log-git", help="Capture the latest Git commit into devmemory")

    subparsers.add_parser("setup", help="Configure API keys for devmemory")

    subparsers.add_parser("setup-antigravity", help="Connect devmemory MCP to Antigravity IDE")
   
    subparsers.add_parser("setup-claude", help="Connect devmemory MCP to Claude Code")


    args = parser.parse_args()

    db_path = Path.home() / ".devmemory" / "store.db"
    
    if args.command == "log":
        with console.status("[bold cyan]Processing memory with AI...[/bold cyan]", spinner="dots"):
            memory = Memory(db_path=db_path)
            memory.capture(source="manual", raw_text=args.message)
        console.print("\n[bold green]✓[/bold green] [bold]Successfully logged memory to devmemory![/bold]\n")
        
    elif args.command == "search":
        console.print(Rule("[bold magenta]🧠 devmemory[/bold magenta]", style="dim"))
        
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

            # Header badge + title summary
            title_text = f"[{badge_style}] {record.type.value.upper()} [/{badge_style}]  [bold white]{record.summary}[/bold white]"

            body_lines = [
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

        devmemory_path = shutil.which("devmemory")
        if devmemory_path:
            bash_path = devmemory_path.replace("\\", "/").replace("C:/", "/c/")
        else:
            bash_path = "devmemory"

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
            memory.capture(source="git")
        console.print("\n[bold green]✓[/bold green] [bold]Captured Git commit memory![/bold]\n")

    elif args.command == "setup":
        console.print("\n[bold cyan]🧠 Welcome to devmemory setup![/bold cyan]\n")

        config = load_config()

        groq_key = input("🔑 Enter your Groq API key: ").strip()
        google_key = input("🔑 Enter your Google API key: ").strip()

        config["groq_api_key"] = groq_key
        config["google_api_key"] = google_key

        save_config(config)

        console.print(f"\n[bold green]✓[/bold green] API keys saved to [cyan]{CONFIG_FILE}[/cyan]")
        console.print("[bold green]✓[/bold green] You're all set! Try: [cyan]devmemory log \"my first memory\"[/cyan]\n")

    elif args.command == "setup-antigravity":
        console.print("\n[bold cyan]>> Connecting devmemory to Antigravity...[/bold cyan]\n")

        config = load_config()
        if not config.get("groq_api_key") or not config.get("google_api_key"):
            console.print("[bold red]✗[/bold red] API keys not found! Run [cyan]devmemory setup[/cyan] first.\n")
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

        mcp_data["mcpServers"]["devmemory"] = {
            "command": python_path,
            "args": ["-m", "devmemory.mcp_server"],
            "env": {
                "GROQ_API_KEY": config["groq_api_key"],
                "GOOGLE_API_KEY": config["google_api_key"],
            }
        }

        with open(mcp_config_path, "w") as f:
            json.dump(mcp_data, f, indent=2)

        console.print(f"[bold green]✓[/bold green] Added devmemory MCP server to [cyan]{mcp_config_path}[/cyan]")
        console.print("[bold green]✓[/bold green] Restart Antigravity to activate! 🚀\n")

    elif args.command == "setup-claude":
        console.print("\n[bold cyan]>> Connecting devmemory to Claude Code...[/bold cyan]\n")

        config = load_config()
        if not config.get("groq_api_key") or not config.get("google_api_key"):
            console.print("[bold red]✗[/bold red] API keys not found! Run [cyan]devmemory setup[/cyan] first.\n")
            return

        claude_config_path = Path.home() / ".claude.json"

        try:
            claude_data = json.load(open(claude_config_path, "r"))
        except (FileNotFoundError, json.JSONDecodeError):
            claude_data = {"mcpServers": {}}

        python_path = shutil.which("python") or "python"

        claude_data.setdefault("mcpServers", {})
        claude_data["mcpServers"]["devmemory"] = {
            "command": python_path,
            "args": ["-m", "devmemory.mcp_server"],
            "env": {
                "GROQ_API_KEY": config["groq_api_key"],
                "GOOGLE_API_KEY": config["google_api_key"],
            }
        }

        with open(claude_config_path, "w") as f:
            json.dump(claude_data, f, indent=2)

        console.print(f"[bold green][OK][/bold green] Added devmemory MCP server to [cyan]{claude_config_path}[/cyan]")
        console.print("[bold green][OK][/bold green] Restart Claude Code to activate!\n")


if __name__ == "__main__":
    main()
