import argparse
from pathlib import Path
from devmemory import Memory

def main():
    # Setup the parser
    parser = argparse.ArgumentParser(description="devmemory CLI")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # 2. Add the 'log' command
    log_parser = subparsers.add_parser("log", help="Log a manual memory")

    log_parser.add_argument("message", type=str, help="The text you want to remember")

    # 3. Add the 'search' command
    search_parser = subparsers.add_parser("search", help="Search your memories")
    search_parser.add_argument("query", type=str, help="What you want to search for")

    subparsers.add_parser("install-hook", help="Install post-commit Git hook")
    
    subparsers.add_parser("log-git", help="Capture the latest Git commit into devmemory")

    # 4. Parse whatever the user typed in the terminal!
    args = parser.parse_args()

    # 5. Start up our Library (the "Kitchen")
    db_path = Path.home() / ".devmemory" / "store.db"
    memory = Memory(db_path=db_path)
    
    # 6. Hand the order to the kitchen based on what the user typed!
    if args.command == "log":
        memory.capture(source="manual", raw_text=args.message)
        print("✅ Successfully logged to devmemory!")
        
    elif args.command == "search":
        print(f"🔍 Searching for: '{args.query}'...\n")
        results = memory.search(args.query)
        
        if not results:
            print("No memories found!")
            
        for record in results:
            print(f"- [{record.type.value}] {record.summary}")
            print(f"  Reasoning: {record.reasoning}\n")

    elif args.command == "install-hook":
        git_dir = Path.cwd() / ".git"
        if not git_dir.exists():
            print("❌ Error: Not a git repository! Run this command inside a git repository.")
            return

        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        hook_path = hooks_dir / "post-commit"

        hook_script = "#!/bin/sh\ndevmemory log-git > /dev/null 2>&1 &\n"
        hook_path.write_text(hook_script, encoding="utf-8")

        try:
            hook_path.chmod(0o755)
        except Exception:
            pass

        print(f"✅ Successfully installed Git post-commit hook into {hook_path}")

    elif args.command == "log-git":
        memory.capture(source="git")
        print("✅ Captured Git commit memory!")


if __name__ == "__main__":
    main()
