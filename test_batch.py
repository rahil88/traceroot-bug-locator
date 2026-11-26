import json
import os

os.environ["TRACEROOT_ENABLED"] = "false"  # tests never send traces

from run_batch import run_batch


def fake_run(n, model, session_id=None):
    if n == 2:
        raise RuntimeError("model crashed")
    return {"issue": n, "model": model, "answer": ["a.py"], "stop": "answer", "calls": [{}], "seconds": 1.0,
            "session": session_id}


def test_batch_writes_each_result_and_survives_a_crash(tmp_path):
    out = run_batch("m", issues=[1, 2, 3], out=tmp_path / "m.jsonl", run=fake_run)
    rows = [json.loads(l) for l in out.read_text().splitlines()]
    assert [r["issue"] for r in rows] == [1, 2, 3]
    assert rows[1]["stop"] == "crash" and "model crashed" in rows[1]["error"]
    assert rows[0]["session"] == "batch-m"


def test_batch_resumes(tmp_path):
    out = tmp_path / "m.jsonl"
    out.write_text(json.dumps({"issue": 1}) + "\n")
    seen = []
    run_batch("m", issues=[1, 3], out=out, run=lambda n, m, session_id=None: seen.append(n) or fake_run(n, m))
    assert seen == [3]
