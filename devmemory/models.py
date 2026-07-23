from datetime import datetime
from typing import Literal
from pydantic import BaseModel
from enum import Enum

class RawEvent(BaseModel):
    id : str
    source : Literal["git", "manual", "chatlog", "ci", "webhook"]
    raw_text : str
    metadata : dict
    timestamp : datetime
    processed : bool = False

class MemoryType(str, Enum):
    DECISION = "decision"
    BUG_FIX = "bug_fix"
    MIGRATION = "migration"
    EXPERIMENT = "experiment"
    API_FAILURE = "api_failure"
    NOTE = "note"

class MemoryRecord(BaseModel):
    id : str
    raw_event_id : str
    type : MemoryType
    summary : str
    reasoning : str
    tags : list[str]
    related_files : list[str]
    source_ref : str
    timestamp : datetime
    embedding : list[float] | None = None
