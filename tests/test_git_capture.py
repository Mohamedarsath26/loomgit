import subprocess
from pathlib import Path
from devmemory import Memory
from devmemory.capture.git import get_last_commit_info

def test_get_last_commit_info(tmp_path: Path):
    # 1. Initialize a real temporary Git repository
    subprocess.run(["git", "init"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)

    # 2. Create a dummy file and commit it
    test_file = tmp_path / "sample.py"
    test_file.write_text("print('hello world')\n")
    
    subprocess.run(["git", "add", "sample.py"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "feat: add sample script"], cwd=tmp_path, check=True)

    # 3. Test our git extraction function
    info = get_last_commit_info(repo_path=tmp_path)

    assert info["message"] == "feat: add sample script"
    assert info["author"] == "Test User <test@example.com>"
    assert "sample.py" in info["changed_files"]
    assert len(info["commit_hash"]) == 40
