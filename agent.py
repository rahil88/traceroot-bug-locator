"""Bug locator: reads one issue, searches the pre-fix code, names the files to fix.

uv run agent.py 1218 [model]

Traced with TraceRoot when run this way. Importing it (tests, scripts) sends nothing
until traceroot.initialize() is called.
"""
import json
import sys
import time
from pathlib import Path

from openai import OpenAI, OpenAIError
from traceroot import observe, update_current_span, update_current_trace

from tools import SCHEMAS, Tools

DEFAULT_MODEL = "qwen2.5-3b-16k"
MAX_CALLS = 12
MAX_HISTORY_CHARS = 36_000  # leaves room for the reply inside 16384 tokens
TRIMMED = "[trimmed]"
SYSTEM = """You find which source files must change to fix a bug.
Use grep to search the code and read_file to check a file. Base your answer on files you found, not on guesses.
When you know, call answer with 1 to 3 file paths. You have at most 12 tool calls."""
REMINDER = "Use a tool. Call grep or read_file to look further, or answer to finish."


def ollama():
    return OpenAI(base_url="http://localhost:11434/v1", api_key="ollama", max_retries=0, timeout=300)


@observe(name="bug-locator", type="agent", capture_input=False)
def run(number, model=DEFAULT_MODEL, client=None, log=lambda line: None):
    issue = json.loads(Path(f"data/issues/{number}.json").read_text())
    text = f"{issue['title']}\n\n{issue['body'] or ''}"
    update_current_span(input={"issue": number, "model": model, "text": text})
    result = {"issue": number, "model": model,
              **run_loop(text, Tools(f"data/trees/{number}"), model, client or ollama(), log)}
    errors = sum(c["error"] for c in result["calls"])
    update_current_trace(
        tags=[f"issue:{number}", f"model:{model}", f"stop:{result['stop']}"],
        metadata={"issue": number, "model": model, "stop": result["stop"], "answer": result["answer"],
                  "calls": len(result["calls"]), "tool_errors": errors, "seconds": result["seconds"],
                  "max_prompt_tokens": result["max_prompt_tokens"]})
    return result


def run_loop(text, tools, model, client, log=lambda line: None):
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}]
    started, calls, silent = time.time(), [], 0
    max_prompt_tokens, error = 0, None

    while True:
        trim(messages)
        try:
            reply = client.chat.completions.create(
                model=model, messages=messages, tools=SCHEMAS, max_tokens=2048,
                temperature=0, seed=0, presence_penalty=0)  # the 4B model defaults to 1 and 1.5
        except OpenAIError as e:
            stop, error = "model_error", f"{type(e).__name__}: {e}"
            break
        if reply.usage:
            max_prompt_tokens = max(max_prompt_tokens, reply.usage.prompt_tokens)
        message = reply.choices[0].message

        if not message.tool_calls:
            silent += 1
            log(f"no tool call: {(message.content or '')[:120]!r}")
            if silent == 2:
                stop = "no_tool_call"
                break
            messages += [{"role": "assistant", "content": message.content or ""}, {"role": "user", "content": REMINDER}]
            continue

        silent = 0
        batch = message.tool_calls[:MAX_CALLS - len(calls)]
        messages.append({"role": "assistant", "content": message.content or "", "tool_calls": [
            {"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}}
            for c in batch]})
        for c in batch:
            result = call_tool(tools, c.function.name, c.function.arguments)
            calls.append({"tool": c.function.name, "arguments": c.function.arguments, "error": result.startswith("error:")})
            log(f"{len(calls)}. {c.function.name} {c.function.arguments[:120]} -> {result.splitlines()[0][:100]}")
            if tools.final:
                break
            messages.append({"role": "tool", "tool_call_id": c.id, "content": result + calls_left(MAX_CALLS - len(calls))})
        if tools.final:
            stop = "answer"
            break
        if len(calls) >= MAX_CALLS:
            stop = "max_calls"
            break

    return {"answer": tools.final or [], "stop": stop, "error": error, "calls": calls,
            "max_prompt_tokens": max_prompt_tokens, "seconds": round(time.time() - started, 1)}


@observe(type="tool", capture_input=False, capture_output=False)
def call_tool(tools, name, arguments):
    """One span per tool call, named after the tool. A tool error is text, so the span stays OK."""
    result = tools.call(name, arguments)
    try:
        shown = json.loads(arguments or "{}")
    except json.JSONDecodeError:
        shown = arguments
    update_current_span(name=name, input=shown, output=result,
                        metadata={"tool_error": result.startswith("error:")})
    return result


def calls_left(n):
    return "\n[1 tool call left, use answer now]" if n == 1 else f"\n[{n} tool calls left]"


def trim(messages):
    """Replace the oldest tool results until the history fits. The newest result is always kept."""
    size = sum(len(json.dumps(m)) for m in messages)
    results = [m for m in messages if m["role"] == "tool" and m["content"] != TRIMMED]
    for m in results[:-1]:
        if size <= MAX_HISTORY_CHARS:
            return
        size -= len(m["content"]) - len(TRIMMED)
        m["content"] = TRIMMED


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    import traceroot
    from dotenv import load_dotenv
    from traceroot import Integration

    load_dotenv()
    traceroot.initialize(integrations=[Integration.OPENAI])
    try:
        result = run(int(sys.argv[1]), *sys.argv[2:3], log=print)
    finally:
        traceroot.flush()
    print(json.dumps({k: v for k, v in result.items() if k != "calls"}, indent=2), f"\n{len(result['calls'])} calls")
