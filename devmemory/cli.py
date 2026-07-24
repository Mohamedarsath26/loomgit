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

if __name__ == "__main__":
    main()
