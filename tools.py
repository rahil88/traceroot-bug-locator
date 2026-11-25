"""The three tools the agent can use on one pre-fix code tree.

Every problem comes back as text starting with "error:", so the model can recover.
"""
import json
from pathlib import Path

MAX_MATCHES = 30
MAX_PER_FILE = 3  # one noisy file must not hide the others
MAX_LINES = 150
MAX_CHARS = 6000
MAX_FILE_BYTES = 500_000
MAX_ANSWERS = 3
SKIP_NAMES = {"pnpm-lock.yaml", "package-lock.json", "yarn.lock", "uv.lock"}


def _schema(name, description, properties, required):
    return {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object", "properties": properties, "required": required}}}


SCHEMAS = [
    _schema("grep", "Find plain text in the code, ignoring case. Returns path:line: text.",
            {"pattern": {"type": "string", "description": "Plain text, not a regex"}}, ["pattern"]),
    _schema("read_file", f"Read up to {MAX_LINES} lines of one file.",
            {"path": {"type": "string", "description": "Path as shown by grep"},
             "start": {"type": "integer", "description": "First line, default 1"}}, ["path"]),
    _schema("answer", f"Give the final answer: 1 to {MAX_ANSWERS} files that need to change. Ends the run.",
            {"paths": {"type": "array", "items": {"type": "string"}}}, ["paths"]),
]


def _is_test_or_doc(path):
    p = path.lower()
    return "test" in p or p.startswith("docs/") or p.endswith((".md", ".mdx"))


class Tools:
    def __init__(self, tree):
        self.tree = Path(tree).resolve()
        if not self.tree.is_dir():
            raise ValueError(f"no such tree: {tree}")
        self.final = None  # paths given to answer()
        self._files = None  # path -> lines, loaded on the first grep

    def call(self, name, arguments):
        """Run one tool call from the model. `arguments` is the raw JSON string."""
        tool = {"grep": (self.grep, ("pattern",)),
                "read_file": (self.read_file, ("path", "start")),
                "answer": (self.answer, ("paths",))}.get(name)
        if tool is None:
            return f"error: unknown tool {name!r}, use grep, read_file or answer"
        try:
            args = json.loads(arguments or "{}")
        except json.JSONDecodeError:
            return "error: arguments are not valid JSON"
        if not isinstance(args, dict):
            return "error: arguments must be a JSON object"
        func, allowed = tool
        return func(**{k: v for k, v in args.items() if k in allowed})  # drop invented arguments

    def grep(self, pattern=None):
        if not isinstance(pattern, str) or not pattern.strip():
            return "error: grep needs a non-empty pattern"
        needle = pattern.strip().lower()
        hits, total, in_files = [], 0, 0
        for path, lines in self._load().items():
            found = [(i, line) for i, line in enumerate(lines, 1) if needle in line.lower()]
            total += len(found)
            in_files += bool(found)
            hits += [f"{path}:{i}: {line.strip()[:160]}" for i, line in found[:MAX_PER_FILE]]
        if not hits:
            return f"no matches for {pattern!r}, try a shorter or different word"
        shown = _fit(hits[:MAX_MATCHES])
        return "\n".join([f"{total} matches in {in_files} files, showing {len(shown)}"] + shown)

    def read_file(self, path=None, start=1):
        target, error = self._resolve(path)
        if error:
            return error
        try:
            start = max(1, int(start))
        except (TypeError, ValueError):
            start = 1
        if target.stat().st_size > MAX_FILE_BYTES:
            return "error: file is too large"
        lines = target.read_text(errors="replace").splitlines()
        if start > max(1, len(lines)):
            return f"error: file has only {len(lines)} lines"
        shown = _fit([f"{i}: {line[:300]}" for i, line in enumerate(lines[start - 1:start - 1 + MAX_LINES], start)])
        last = start + len(shown) - 1
        more = f", use start={last + 1} for more" if last < len(lines) else ""
        rel = target.relative_to(self.tree)
        return "\n".join([f"{rel} lines {start}-{last} of {len(lines)}{more}"] + shown)

    def answer(self, paths=None):
        if isinstance(paths, str):  # small models often send a string
            try:
                paths = json.loads(paths)
            except json.JSONDecodeError:
                paths = paths.split(",")
        if isinstance(paths, str):
            paths = [paths]
        if not isinstance(paths, list) or not all(isinstance(p, str) for p in paths):
            return "error: paths must be a list of file paths"
        paths = list(dict.fromkeys(_clean(p) for p in paths if p.strip()))
        if not 1 <= len(paths) <= MAX_ANSWERS:
            return f"error: give 1 to {MAX_ANSWERS} paths, you gave {len(paths)}"
        self.final = paths  # not checked on purpose: invented paths are a failure we want to count
        return "answer recorded"

    def _resolve(self, path):
        if not isinstance(path, str) or not path.strip():
            return None, "error: read_file needs a path"
        target = (self.tree / _clean(path)).resolve()
        if not target.is_relative_to(self.tree):
            return None, "error: path is outside the code tree"
        if target.is_dir():
            return None, "error: that is a directory, use grep to find files"
        if not target.is_file():
            return None, f"error: no such file {path!r}, use a path shown by grep"
        return target, None

    def _load(self):
        if self._files is None:
            found = {}
            for f in self.tree.rglob("*"):
                if f.is_symlink() or not f.is_file() or f.name in SKIP_NAMES or f.stat().st_size > MAX_FILE_BYTES:
                    continue
                data = f.read_bytes()
                if b"\0" not in data:  # skip binary files
                    found[f.relative_to(self.tree).as_posix()] = data.decode(errors="replace").splitlines()
            # source code first, so tests and docs do not fill the 30 results
            self._files = dict(sorted(found.items(), key=lambda kv: (_is_test_or_doc(kv[0]), kv[0])))
        return self._files


def _clean(path):
    return path.strip().strip("\"'`").removeprefix("./").lstrip("/")


def _fit(lines):
    """Keep whole lines up to MAX_CHARS, always at least one."""
    kept, size = [], 0
    for line in lines:
        size += len(line) + 1
        if kept and size > MAX_CHARS:
            break
        kept.append(line)
    return kept
