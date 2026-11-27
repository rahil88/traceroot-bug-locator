"""Second look at the batch: score against every file in the real PR, and label each failure.

uv run analyze.py

Labels come from the run logs by fixed rules, checked in order:
  gave up           0 tool calls
  opened then dropped  read a file from the real fix, then did not answer with it
  invented path     2 or more reads of files that do not exist
  loop              3 or more repeats of the exact same call
  wrong file        answered, but no file is in the real fix
  bad search        anything else (searched, never found the right file)
results/fix_pr_files.json lists every file the fix PR changed (from the GitHub API),
including tests and config that data/answers.json leaves out.
"""
import json
from collections import Counter
from pathlib import Path

from score import load_truth

RUNNERS = ["baseline", "qwen2.5-3b-16k", "qwen3.5-4b-16k"]


def label(run, key):
    calls = [(c["tool"], c["arguments"]) for c in run["calls"]]
    reads = [json.loads(a).get("path") for t, a in calls if t == "read_file"]
    read_errors = sum(c["error"] for c in run["calls"] if c["tool"] == "read_file")
    repeats = sum(n - 1 for n in Counter(calls).values() if n > 1)
    if not calls:
        return "gave up"
    if set(reads) & key:
        return "opened then dropped"
    if read_errors >= 2:
        return "invented path"
    if repeats >= 3:
        return "loop"
    if run["answer"]:
        return "wrong file"
    return "bad search"


def main():
    key = load_truth()
    full = {int(n): set(v["files"]) for n, v in json.loads(Path("results/fix_pr_files.json").read_text()).items()}
    print("| Runner | Hits, source files key | Hits, any file in the real PR |\n|---|---|---|")
    for name in RUNNERS:
        runs = [json.loads(l) for l in Path(f"results/{name}.jsonl").read_text().splitlines()]
        print(f"| {name} | {sum(bool(set(r['answer']) & set(key[r['issue']])) for r in runs)}/15 "
              f"| {sum(bool(set(r['answer']) & full[r['issue']]) for r in runs)}/15 |")

    print("\n| Model | Issue | Ended | Label | Calls | Max prompt tokens |\n|---|---|---|---|---|---|")
    counts = Counter()
    for name in RUNNERS[1:]:
        for line in Path(f"results/{name}.jsonl").read_text().splitlines():
            r = json.loads(line)
            if set(r["answer"]) & full[r["issue"]]:
                continue
            lab = label(r, set(key[r["issue"]]))
            counts[lab] += 1
            print(f"| {name} | {r['issue']} | {r['stop']} | {lab} | {len(r['calls'])} | {r['max_prompt_tokens']} |")
    print("\n" + ", ".join(f"{k} {v}" for k, v in counts.most_common()) + f" (total {sum(counts.values())})")


if __name__ == "__main__":
    main()
