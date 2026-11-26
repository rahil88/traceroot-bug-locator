"""No-LLM baseline: rank source files by the issue's keywords and answer the top 3.

uv run baseline.py   writes results/baseline.jsonl

If the agent cannot beat this, the model is not adding much over plain search.
"""
import json
import math
import re
import time
from pathlib import Path

from tools import Tools, _is_test_or_doc

SOURCE = (".py", ".ts", ".tsx", ".js", ".jsx")
STOP = set("""should would could their there these those which while where after before about other being
    because always without within between expected actual summary steps reproduce behavior behaviour
    instead issue problem currently either really string number return value values default""".split())


def keywords(text):
    words = set()
    for code in re.findall(r"`([^`\n]{3,80})`", text):
        words |= set(re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}", code))
    words |= set(re.findall(r"\b[a-z]+[A-Z][A-Za-z0-9]*\b|\b[A-Z][a-z0-9]+[A-Z][A-Za-z0-9]*\b", text))
    words |= set(re.findall(r"\b[a-z0-9]+_[a-z0-9_]+\b", text))
    words |= {w.lower() for w in re.findall(r"\b[A-Za-z]{6,}\b", text)} - STOP
    return sorted(words)


def rank(tree, words, top=3):
    files = {p: (p.lower(), "\n".join(lines).lower()) for p, lines in Tools(tree)._load().items()
             if p.endswith(SOURCE) and not _is_test_or_doc(p)}
    n = len(files)
    weight = {}
    for w in {w.lower() for w in words}:
        df = sum(w in text for _, text in files.values())
        if df:
            weight[w] = math.log(n / df)
    scores = {p: sum(wt for w, wt in weight.items() if w in text) + 2 * sum(wt for w, wt in weight.items() if w in path)
              for p, (path, text) in files.items()}
    return sorted(scores, key=lambda p: (-scores[p], p))[:top]


def main():
    out = Path("results/baseline.jsonl")
    out.parent.mkdir(exist_ok=True)
    with out.open("w") as f:
        for issue_file in sorted(Path("data/issues").glob("*.json"), key=lambda p: int(p.stem)):
            issue = json.loads(issue_file.read_text())
            started = time.time()
            answer = rank(f"data/trees/{issue['number']}", keywords(f"{issue['title']}\n{issue['body'] or ''}"))
            f.write(json.dumps({"issue": issue["number"], "model": "keyword-baseline", "answer": answer, "stop": "answer",
                                "seconds": round(time.time() - started, 1)}) + "\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
