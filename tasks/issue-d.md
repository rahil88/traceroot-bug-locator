<!-- DRAFT, not posted. Repo: traceroot-ai/traceroot-py. I edit this and post it myself. Re-check duplicates first. -->

# `@observe` on async functions records `asyncio/events.py` as the source location

**Version:** traceroot 0.5.1, Python 3.12.13, macOS

## What happens

When an `@observe` async function is started by `asyncio.run`, `create_task` or `gather`, its source location is Python's own `asyncio/events.py:88` (`_run`) instead of a line in my code.

The path is also absolute, because it is outside the git root, so it includes the local username.

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

| How it runs | Recorded location |
|---|---|
| `asyncio.run(agent())` | `asyncio/events.py:88`, `_run` |
| `asyncio.create_task(tool())` | `asyncio/events.py:88`, `_run` |
| `asyncio.gather(tool())` | `asyncio/events.py:88`, `_run` |
| `await tool()` | the caller's line in my file, as expected |

## Expected

A line in user code. traceroot-ai/traceroot#1027 says these attributes are meant to be call-site-specific, so I am not questioning that. Here the recorded site is not user code at all.

## Why it matters

- The error box shows this path when a tool fails, which is when someone needs it.
- With GitHub connected, the RCA prompt says to read the source at `git_source_file` and `git_source_line` (`detector-rca-processor.ts`).

## Likely cause

`capture_source_location()` in `git_context.py` skips SDK, OpenTelemetry, OpenInference and `<frozen>` frames, but not the standard library. When the event loop starts the coroutine, the first remaining frame is `asyncio/events.py`.

## Options

1. **Skip standard library frames.** I tried this: `asyncio.run(agent())` then records the correct line. `create_task(tool())` records the `asyncio.run` line, which is my code but not the call site.
2. **Fall back to the decorated function's definition** when the walk reaches the event loop. I have not tried this.

Happy to open a PR for whichever you prefer.
