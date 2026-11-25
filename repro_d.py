"""Lead D: which source line does @observe record? No model needed.

Every tool fails on purpose, because the UI shows the location only on failed spans.
"""
import asyncio

from dotenv import load_dotenv

load_dotenv()

import traceroot
from traceroot import observe

traceroot.initialize()


@observe(name="tool-create-task", type="tool")
async def tool_create_task():
    raise ValueError("failed inside tool_create_task")


@observe(name="tool-await", type="tool")
async def tool_await():
    raise ValueError("failed inside tool_await")


@observe(name="tool-dispatch-a", type="tool")
def tool_dispatch_a():
    raise ValueError("failed inside tool_dispatch_a")


@observe(name="tool-dispatch-b", type="tool")
def tool_dispatch_b():
    raise ValueError("failed inside tool_dispatch_b")


@observe(name="repro-d", type="agent")
async def agent():
    try:
        await asyncio.create_task(tool_create_task())
    except ValueError:
        pass
    try:
        await tool_await()
    except ValueError:
        pass
    for tool in (tool_dispatch_a, tool_dispatch_b):
        try:
            tool()
        except ValueError:
            pass
    try:
        await asyncio.gather(tool_gather())
    except ValueError:
        pass


# Defined last so the line numbers in notes.md stay the same.
@observe(name="tool-gather", type="tool")
async def tool_gather():
    raise ValueError("failed inside tool_gather")


asyncio.run(agent())
traceroot.flush()
print("sent")
