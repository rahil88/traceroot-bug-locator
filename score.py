"""Score runs against the files the real fixes changed.

uv run score.py results/*.jsonl

A run is a hit if any of its 1 to 3 files is in data/answers.json. Test files are not in
the answers, so a run that also names a test file is not punished, and not rewarded.
"""
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

from tools import _clean

EASY = {1218, 3076}  # the issue text nearly names the answer file


def load_truth(path="data/answers.json"):
    return {int(k): v for k, v in json.loads(Path(path).read_text()).items()}


def score(answer, truth, tree=None):
    given = list(dict.fromkeys(_clean(p) for p in answer))
    right = [p for p in given if p in truth]
    return {"hit": bool(right), "right": right,
            "wrong": [p for p in given if p not in truth],
            "invented": [p for p in given if tree and not (Path(tree) / p).is_file()]}


def load_runs(paths):
    return [json.loads(line) for p in paths for line in Path(p).read_text().splitlines() if line.strip()]


def report(runs, truth, trees="data/trees"):
    by_runner = defaultdict(list)
    for r in runs:
        s = score(r["answer"], truth[r["issue"]], f"{trees}/{r['issue']}")
        by_runner[r["model"]].append({**r, **s})

    lines = ["| Runner | Hits | Hits on 13 harder | Answered | Invented paths | Median s | Stops |",
             "|---|---|---|---|---|---|---|"]
    for runner, rs in by_runner.items():
        hard = [r for r in rs if r["issue"] not in EASY]
        secs = [r["seconds"] for r in rs if r.get("seconds") is not None]
        stops = ", ".join(f"{k} {v}" for k, v in Counter(r["stop"] for r in rs).most_common())
        lines.append(f"| {runner} | {sum(r['hit'] for r in rs)}/{len(rs)} | {sum(r['hit'] for r in hard)}/{len(hard)} "
                     f"| {sum(bool(r['answer']) for r in rs)}/{len(rs)} | {sum(len(r['invented']) for r in rs)} "
                     f"| {statistics.median(secs) if secs else '-'} | {stops} |")

    issues = sorted({r["issue"] for r in runs})
    lines += ["", "| Issue | " + " | ".join(by_runner) + " |", "|---" * (len(by_runner) + 1) + "|"]
    for n in issues:
        cells = []
        for rs in by_runner.values():
            r = next((r for r in rs if r["issue"] == n), None)
            cells.append("" if r is None else "hit" if r["hit"] else "no answer" if not r["answer"] else "miss")
        lines.append(f"| {n}{' (easy)' if n in EASY else ''} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    print(report(load_runs(sys.argv[1:]), load_truth()))
