import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".loomgit"
CONFIG_FILE = CONFIG_DIR / "config.json"
LEGACY_CONFIG_FILE = Path.home() / ".devloom" / "config.json"

def load_config() -> dict:
    """Reads the config file and returns it as a dictionary."""
    if not CONFIG_FILE.exists() and LEGACY_CONFIG_FILE.exists():
        with open(LEGACY_CONFIG_FILE, "r") as f:
            return json.load(f)
    if not CONFIG_FILE.exists():
        return {}
    
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config: dict) -> None:
    """Saves the config dictionary to the config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def get_key(key_name: str) -> str | None:
    """Gets an API key: first checks config.json, then falls back to environment variable."""
    config = load_config()
    
    value = config.get(key_name)
    if value:
        return value
    
    import os
    return os.getenv(key_name.upper())
