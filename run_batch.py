"""Run the agent on all 15 issues with one model, traced.

uv run run_batch.py qwen2.5-3b-16k
uv run run_batch.py qwen3.5-4b-16k

Each result is appended to results/<model>.jsonl as soon as it finishes, so a stopped
batch picks up where it left off. All runs share one TraceRoot session per model.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import agent
from prepare_data import ISSUES


def done_issues(out):
    if not out.exists():
        return set()
    return {json.loads(line)["issue"] for line in out.read_text().splitlines() if line.strip()}


def run_batch(model, issues=ISSUES, out=None, run=agent.run, flush=lambda: None):
    out = Path(out or f"results/{model}.jsonl")
    out.parent.mkdir(exist_ok=True)
    skip = done_issues(out)
    session = f"batch-{model}"
    todo = [n for n in issues if n not in skip]
    print(f"{model}: {len(todo)} to run, {len(skip)} already done")
    for i, n in enumerate(todo, 1):
        started = time.time()
        try:
            result = run(n, model, session_id=session)
        except Exception as e:  # one broken run must not stop the batch
            result = {"issue": n, "model": model, "answer": [], "stop": "crash",
                      "error": f"{type(e).__name__}: {e}", "calls": [], "seconds": round(time.time() - started, 1)}
        finally:
            flush()  # send each trace now, not at the end
        with out.open("a") as f:
            f.write(json.dumps(result) + "\n")
        print(f"[{i}/{len(todo)}] #{n} {result['stop']}, {len(result['calls'])} calls, {result['seconds']} s, "
              f"answer {[p.split('/')[-1] for p in result['answer']]}", flush=True)
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    import traceroot
    from dotenv import load_dotenv
    from traceroot import Integration

    load_dotenv()
    traceroot.initialize(integrations=[Integration.OPENAI])
    model = sys.argv[1]
    try:
        print(f"wrote {run_batch(model, flush=traceroot.flush)}")
    finally:
        traceroot.flush()
        subprocess.run(["ollama", "stop", model], check=False)
