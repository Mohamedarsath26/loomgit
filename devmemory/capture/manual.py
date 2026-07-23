import uuid
from datetime import datetime
from devmemory.models import RawEvent

def create_manual_event(text: str) -> RawEvent:
    """Takes a simple text note and turns it into a RawEvent ready for the database."""
    
    # 1. We create the real Object from our Blueprint!
    event = RawEvent(
        id=str(uuid.uuid4()),
        source="manual",
        raw_text=text,
        metadata={},  # Manual notes don't need any special metadata right now
        timestamp=datetime.now(),
        processed=False # It's brand new, so it hasn't gone through AI extraction yet!
    )
    
    return event
