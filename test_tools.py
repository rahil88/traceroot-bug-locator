import json

import pytest

from tools import MAX_CHARS, MAX_MATCHES, Tools


@pytest.fixture
def tools(tmp_path):
    tree = tmp_path / "tree"
    (tree / "src").mkdir(parents=True)
    (tree / "tests").mkdir()
    (tree / "src" / "app.py").write_text("\n".join(f"line {i} Widget" for i in range(1, 401)))
    (tree / "src" / "other.py").write_text("widget = 1\n")
    (tree / "src" / "empty.py").write_text("")
    (tree / "src" / "wide.py").write_text("\n".join("x" * 250 for _ in range(200)))
    (tree / "tests" / "test_app.py").write_text("widget\n")
    (tree / "logo.png").write_bytes(b"widget\0\1")
    (tmp_path / "answers.json").write_text("secret")
    (tree / "link.py").symlink_to(tmp_path / "answers.json")
    return Tools(tree)


def call(tools, name, **args):
    return tools.call(name, json.dumps(args))


def test_grep_ignores_case_and_caps_each_file(tools):
    out = call(tools, "grep", pattern="WIDGET").splitlines()
    assert out[0] == "402 matches in 3 files, showing 5"
    assert sum(l.startswith("src/app.py") for l in out) == 3
    assert out[-1].startswith("tests/")  # tests come last
    assert "logo.png" not in "\n".join(out)


def test_grep_is_plain_text_and_capped(tools, tmp_path):
    for i in range(60):
        (tmp_path / "tree" / f"f{i}.py").write_text("a(b*\n")
    out = call(tools, "grep", pattern="a(b*").splitlines()
    assert len(out) == MAX_MATCHES + 1


def test_grep_problems_are_text(tools):
    assert call(tools, "grep", pattern="zzz").startswith("no matches")
    assert call(tools, "grep", pattern=" ").startswith("error:")
    assert call(tools, "grep").startswith("error:")


def test_read_file_pages(tools):
    assert call(tools, "read_file", path="src/app.py").startswith("src/app.py lines 1-150 of 400, use start=151")
    assert call(tools, "read_file", path="/src/app.py", start="390").startswith("src/app.py lines 390-400 of 400\n")
    assert call(tools, "read_file", path="src/empty.py").startswith("src/empty.py")
    assert call(tools, "read_file", path="src/app.py", start=999).startswith("error:")


def test_read_file_char_cap_reports_the_real_last_line(tools):
    out = call(tools, "read_file", path="src/wide.py")
    last = int(out.splitlines()[-1].split(":")[0])
    assert f"lines 1-{last} of 200, use start={last + 1}" in out
    assert len(out) < MAX_CHARS + 200


@pytest.mark.parametrize("path", ["../answers.json", "../../answers.json", "src/../../answers.json", "link.py",
                                  "/etc/passwd", "src", "missing.py", "", None, 5])
def test_read_file_refuses(tools, path):
    out = call(tools, "read_file", path=path)
    assert out.startswith("error:") and "secret" not in out


def test_answer_accepts_lists_and_strings(tools):
    for paths in (["./src/app.py", "src/app.py"], '["src/app.py"]', "src/app.py"):
        assert call(tools, "answer", paths=paths) == "answer recorded"
        assert tools.final == ["src/app.py"]


@pytest.mark.parametrize("paths", [[], ["a", "b", "c", "d"], [1], None, {"a": 1}, ""])
def test_answer_refuses(tools, paths):
    assert call(tools, "answer", paths=paths).startswith("error:")
    assert tools.final is None


def test_bad_calls_are_text(tools):
    assert tools.call("rm", "{}").startswith("error: unknown tool")
    assert tools.call("grep", "{bad").startswith("error:")
    assert tools.call("grep", "[1]").startswith("error:")
    assert tools.call("grep", '{"pattern": "widget", "recursive": true}').startswith("402 matches")
