from baseline import keywords
from score import report, score


def test_score_any_file_is_a_hit(tmp_path):
    (tmp_path / "a.py").write_text("")
    s = score(["./a.py", "b.py"], ["a.py", "c.py"], tmp_path)
    assert s == {"hit": True, "right": ["a.py"], "wrong": ["b.py"], "invented": ["b.py"]}
    assert score([], ["a.py"])["hit"] is False


def test_report_counts_easy_and_no_answer():
    runs = [{"issue": 1218, "model": "m", "answer": ["x.py"], "stop": "answer", "seconds": 2},
            {"issue": 9, "model": "m", "answer": [], "stop": "max_calls", "seconds": 4}]
    out = report(runs, {1218: ["x.py"], 9: ["y.py"]}, trees="nowhere")
    assert "| m | 1/2 | 0/1 | 1/2 | 1 | 3.0 | answer 1, max_calls 1 |" in out
    assert "| 1218 (easy) | hit |" in out and "| 9 | no answer |" in out


def test_keywords_pick_code_names_not_prose():
    k = keywords("The `ModelSelector` resets on refresh because getDefault uses llm_models. Expected it should work.")
    assert {"ModelSelector", "getDefault", "llm_models", "refresh"} <= set(k)
    assert "should" not in k and "expected" not in k
