import uuid
from datetime import datetime
from loomgit.models import RawEvent
from pathlib import Path

def create_manual_event(text: str, cwd: Path | str | None = None) -> RawEvent:
    """Takes a simple text note and turns it into a RawEvent ready for the database."""

    folder = Path(cwd).resolve() if cwd else Path.cwd().resolve()
    
    # 1. We create the real Object from our Blueprint!
    event = RawEvent(
        id=str(uuid.uuid4()),
        source="manual",
        raw_text=text,
        metadata={},  # Manual notes don't need any special metadata right now
        timestamp=datetime.now(),
        processed=False ,# It's brand new, so it hasn't gone through AI extraction yet!,
        project_path=str(folder),
        project_name=folder.name,
    )
    
    return event
