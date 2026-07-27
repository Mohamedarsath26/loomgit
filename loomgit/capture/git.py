import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from loomgit.models import RawEvent


def _run_git_command(args: list[str], cwd: Path | str | None = None) -> str:
    """Executes a git command using subprocess and returns its stdout output."""
    cmd = ["git"] + args
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True
    )
    return result.stdout.strip()


def get_last_commit_info(repo_path: Path | str | None = None) -> dict:
    """Extracts metadata, changed files, and code diff for the latest git commit."""
    commit_hash = _run_git_command(["rev-parse", "HEAD"], cwd=repo_path)
    author = _run_git_command(["log", "-1", "--format=%an <%ae>"], cwd=repo_path)
    message = _run_git_command(["log", "-1", "--format=%B"], cwd=repo_path)
    
    # Extract modified file list
    raw_files = _run_git_command(["show", "--name-only", "--format=", "HEAD"], cwd=repo_path)
    changed_files = [f for f in raw_files.splitlines() if f.strip()]
    
    # Extract code diff (exclude commit log header to prevent LLM prompt confusion)
    diff = _run_git_command(["show", "--format=", "HEAD"], cwd=repo_path)
    
    return {
        "commit_hash": commit_hash,
        "author": author,
        "message": message,
        "changed_files": changed_files,
        "diff": diff
    }


def create_git_event(repo_path: Path | str | None = None) -> RawEvent:
    """Extracts git commit details and converts them into a RawEvent object."""
    info = get_last_commit_info(repo_path)
    
    event = RawEvent(
        id=str(uuid.uuid4()),
        source="git",
        raw_text=info["message"],
        metadata={
            "commit_hash": info["commit_hash"],
            "author": info["author"],
            "changed_files": info["changed_files"],
            "diff": info["diff"],
        },
        timestamp=datetime.now(),
        processed=False
    )
    
    return event
