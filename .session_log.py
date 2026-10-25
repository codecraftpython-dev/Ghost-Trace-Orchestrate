from pathlib import Path
import subprocess
from datetime import datetime, timezone

root = Path(r"d:\Professional work\GIT\hackerrank-orchestrate-october26-main\hackerrank-orchestrate-october26-main")
log_path = root / "log.txt"
branch = "unknown"
try:
    branch = subprocess.check_output(["git", "-C", str(root), "branch", "--show-current"], text=True, stderr=subprocess.STDOUT).strip() or "unknown"
except Exception:
    pass
stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
entry = (
    "## " + stamp + " SESSION START\n"
    + "tool=GitHub Copilot\n"
    + "model=MAI-Code-1.1-Flash\n"
    + "Repo Root: " + str(root) + "\n"
    + "Branch: " + branch + "\n"
    + "Worktree: main\n"
    + "Parent Agent: none\n"
    + "Language: py\n"
    + "Time Remaining: not configured\n\n"
)
with log_path.open("a", encoding="utf-8", newline="\n") as f:
    f.write(entry)
print(log_path)
print(entry)
