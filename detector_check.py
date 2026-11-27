"""Fetch the TraceRoot detector's verdict for every batch run and put it next to the score.

uv run detector_check.py

Reads results/qwen*.jsonl (trace_id per run), asks the public API for each trace's
finding, and writes results/detector.jsonl. No finding (HTTP 404) means the detector
ran and did not flag the trace (sampling is 100%). Needs TRACEROOT_API_KEY in .env.
"""
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

from score import load_truth, score


def finding(trace_id, key, host):
    req = urllib.request.Request(
        f"{host}/api/v1/public/detectors/traces/{trace_id}/finding",
        headers={"Authorization": f"Bearer {key}", "User-Agent": "bug-locator"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def main():
    load_dotenv()
    key = os.environ["TRACEROOT_API_KEY"]
    host = os.environ.get("TRACEROOT_HOST_URL", "https://app.traceroot.ai").rstrip("/")
    truth = load_truth()
    rows = []
    for path in sorted(Path("results").glob("qwen*.jsonl")):
        for line in path.read_text().splitlines():
            run = json.loads(line)
            f = finding(run["trace_id"], key, host)
            result = (f or {}).get("results", [{}])[0]
            rows.append({
                "model": run["model"], "issue": run["issue"], "stop": run["stop"],
                "hit": score(run["answer"], truth[run["issue"]])["hit"],
                "flagged": bool(f), "signal": result.get("signal_title"),
                "summary": result.get("summary"), "trace_id": run["trace_id"]})
    out = Path("results/detector.jsonl")
    out.write_text("".join(json.dumps(r) + "\n" for r in rows))
    for hit in (False, True):
        group = [r for r in rows if r["hit"] == hit]
        print(f"scorer {'hit' if hit else 'miss'}: {len(group)} runs, detector flagged {sum(r['flagged'] for r in group)}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
