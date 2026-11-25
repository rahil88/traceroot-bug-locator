import json
from types import SimpleNamespace as NS

import pytest
from openai import OpenAIError

import agent
from tools import Tools


class FakeClient:
    """Plays back replies. A reply is a list of (tool, args) calls, a string, or an exception."""

    def __init__(self, replies):
        self.replies, self.seen = list(replies), []
        self.chat = NS(completions=NS(create=self.create))

    def create(self, **kwargs):
        self.seen.append(json.loads(json.dumps(kwargs["messages"])))
        r = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        if isinstance(r, Exception):
            raise r
        calls = None if isinstance(r, str) else [
            NS(id=f"c{i}", function=NS(name=n, arguments=json.dumps(a))) for i, (n, a) in enumerate(r)]
        content = r if isinstance(r, str) else None
        return NS(usage=NS(prompt_tokens=100), choices=[NS(message=NS(content=content, tool_calls=calls))])


@pytest.fixture
def tools(tmp_path):
    (tmp_path / "a.py").write_text("\n".join("widget " + "x" * 200 for _ in range(200)))
    return Tools(tmp_path)


def go(tools, *replies):
    client = FakeClient(replies)
    return agent.run_loop("issue", tools, "m", client), client


GREP = [("grep", {"pattern": "widget"})]
ANSWER = [("answer", {"paths": ["a.py"]})]


def test_answer_ends_the_run(tools):
    r, _ = go(tools, GREP, ANSWER)
    assert (r["stop"], r["answer"], len(r["calls"])) == ("answer", ["a.py"], 2)


def test_stops_at_max_calls(tools):
    r, c = go(tools, GREP)
    assert (r["stop"], r["answer"], len(r["calls"])) == ("max_calls", [], agent.MAX_CALLS)
    assert "use answer now" in c.seen[-1][-1]["content"]


def test_many_calls_in_one_reply_respect_the_limit(tools):
    r, _ = go(tools, GREP * 30)
    assert (r["stop"], len(r["calls"])) == ("max_calls", agent.MAX_CALLS)


def test_one_reminder_then_stop(tools):
    r, c = go(tools, "hmm")
    assert r["stop"] == "no_tool_call" and len(c.seen) == 2
    assert c.seen[1][-1]["content"] == agent.REMINDER


def test_silence_counter_resets(tools):
    r, _ = go(tools, "hmm", GREP, "hmm", ANSWER)
    assert r["stop"] == "answer"


def test_bad_answer_does_not_end_the_run(tools):
    r, _ = go(tools, [("answer", {"paths": []})], ANSWER)
    assert r["stop"] == "answer" and r["calls"][0]["error"]


def test_model_error_is_reported(tools):
    r, _ = go(tools, OpenAIError("boom"))
    assert r["stop"] == "model_error" and "boom" in r["error"]


def test_history_is_trimmed_oldest_first(tools):
    read = [("read_file", {"path": "a.py"})]
    r, c = go(tools, *[read] * 10, ANSWER)
    results = [m["content"] for m in c.seen[-1] if m["role"] == "tool"]
    assert results[0] == agent.TRIMMED and results[-1].startswith("a.py")
    assert all(sum(len(json.dumps(m)) for m in s) <= agent.MAX_HISTORY_CHARS for s in c.seen)
    assert all(m["tool_call_id"] for m in c.seen[-1] if m["role"] == "tool")
