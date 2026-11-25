I was tracing a small async agent and opened a failed tool span to find the bug. The error box pointed to Python's own `asyncio/events.py:88`, not to my code.

traceroot 0.5.1, Python 3.12.13, macOS, TraceRoot Cloud v1.3.10

## Repro

```python
import asyncio
import traceroot
from traceroot import observe

traceroot.initialize()

@observe(type="tool")
async def tool():
    raise ValueError("failed inside tool")

@observe(type="agent")
async def agent():
    try:
        await asyncio.create_task(tool())
    except ValueError:
        pass

asyncio.run(agent())
traceroot.flush()
```

Open the failed `tool` span. The error box shows:

```
/Users/<me>/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/lib/python3.12/asyncio/events.py:88
```

| How the function starts | Recorded location |
|---|---|
| `asyncio.run(agent())` | `asyncio/events.py:88`, `_run` |
| `asyncio.create_task(tool())` | `asyncio/events.py:88`, `_run` |
| `asyncio.gather(tool())` | `asyncio/events.py:88`, `_run` |
| `await tool()` | the calling line in my file |

## Expected

A line in my code. I saw in traceroot-ai/traceroot#1027 that these attributes are meant to be call-site-specific, so `await` looks right to me. In the other three rows the recorded location is not user code.

## Why it matters

- The error box shows this location on failed spans, so it is wrong when I need it most.
- When GitHub is connected, the [RCA prompt](https://github.com/traceroot-ai/traceroot/blob/7f600b20d323648efb3cedbf388b6c902121dd76/frontend/worker/src/processors/detector-rca-processor.ts#L220) tells the agent to read the source at `git_source_file` and `git_source_line`. Here that file is not in my repo.
- The path is outside the git root, so it is sent as an absolute path and includes my local username.

## Cause

[`capture_source_location()`](https://github.com/traceroot-ai/traceroot-py/blob/bea7be13517b613289920b43edf7e793bdcdb258/traceroot/git_context.py#L55) walks up the stack when the wrapped coroutine starts running, and takes the first frame outside the SDK, OpenTelemetry and OpenInference.

- With `await`, the caller is still on the stack, so my file comes first.
- With `create_task`, `gather` and `asyncio.run`, the event loop starts the coroutine, so `events.py` comes first. The standard library is not on the skip list.

## Possible fixes

1. Skip standard library frames. This should fix `asyncio.run`. For `create_task` and `gather` it would not find the real call site, because the function that scheduled the task is no longer on the stack.
2. Capture the location when the decorated function is called, before the coroutine runs.
3. Fall back to the decorated function's definition when no user frame is found.

I have not implemented any of these. If you have a preferred direction, I am happy to open a PR with a test.
