"""Build data/: issue text, pre-fix code and answers for the 15 test issues.

data/issues/<n>.json   what the agent sees
data/trees/<n>/        pre-fix code, no .git, what the tools can read
data/answers.json      files changed by the real fix, only the scorer reads this

Needs git and a logged in gh. Safe to run again: finished issues are skipped.
"""
import io
import json
import re
import subprocess
import tarfile
from pathlib import Path

REPO = "traceroot-ai/traceroot"
ISSUES = [3076, 3075, 3073, 2030, 1568, 1567, 1244, 1224, 1218, 1198, 1154, 857, 625, 557, 556]
DATA = Path("data")
GIT_DIR = DATA / "repo.git"
ROW = re.compile(r"^\| \S+ \| #(\d+) \| #\d+ \| `(\w+)` \| .*? \| (.*?) \|$", re.M)


def run(*cmd):
    return subprocess.run(cmd, check=True, capture_output=True).stdout


def gh(path):
    return json.loads(run("gh", "api", f"repos/{REPO}/{path}"))


def main():
    rows = {int(n): (sha, files.split("<br>")) for n, sha, files in ROW.findall(Path("tasks/candidates.md").read_text())}
    (DATA / "issues").mkdir(parents=True, exist_ok=True)
    if not GIT_DIR.exists():
        run("git", "init", "--bare", "-q", str(GIT_DIR))
    git = ("git", f"--git-dir={GIT_DIR}")

    for n in ISSUES:
        tree = DATA / "trees" / str(n)
        done = DATA / "issues" / f"{n}.json"  # written last, so it marks a finished issue
        if done.exists():
            continue
        short, files = rows[n]
        sha = gh(f"commits/{short}")["sha"]
        run(*git, "fetch", "-q", "--depth", "1", f"https://github.com/{REPO}.git", sha)
        with tarfile.open(fileobj=io.BytesIO(run(*git, "archive", sha))) as tar:
            tar.extractall(tree, filter="data")
        missing = [f for f in files if not (tree / f).is_file()]
        if missing:
            raise SystemExit(f"#{n}: not in the pre-fix tree: {missing}")
        issue = gh(f"issues/{n}")
        done.write_text(
            json.dumps({"number": n, "title": issue["title"], "body": issue["body"]}, indent=2))
        print(f"#{n} {sha[:9]} ok")

    (DATA / "answers.json").write_text(json.dumps({n: rows[n][1] for n in ISSUES}, indent=2))


if __name__ == "__main__":
    main()
