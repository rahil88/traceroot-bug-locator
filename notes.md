# Notes: using TraceRoot

Each entry says how it was seen:
- **Cloud**: in my own TraceRoot project
- **Local test**: sent to a fake server on my Mac, not yet seen in the cloud

Setup: Python SDK 0.5.1, OpenAI client pointed at Ollama, macOS.

## 2026-11-24: onboarding and first trace

**Onboarding screen**
- It leads with a terminal command (`npx traceroot-cli setup`), with "Set up manually" as the second option. I used manual.
- The CLI source says setup has Claude Code or Codex add the SDK. My repo had no app code yet, so there was nothing to instrument.
- The first project was named `my-llm-project`. I renamed it to `bug-locator`.

**Key and env**
- The SDK does not load `.env` by itself. I call `load_dotenv()` before `initialize()`.
- The key check returned project `bug-locator` and scope `ingest`.

**First trace (Cloud)**, `smoke.py`, about 20:30 PST

| Span | Type | Time | Recorded |
|---|---|---|---|
| `first-trace` | AGENT | 2.9 s | `smoke.py:18`, function `<module>` |
| `ChatCompletion` | LLM | 2.8 s | `qwen2.5-3b-16k`, 35 in, 9 out, no cost |

- Worked on the first run. The nesting was right, and the model and tokens were recorded.
- Cost is empty on the span, but the API returns `total_cost: 0.0` for the trace. Already reported (#2736), skip.
- The commit it recorded (`ca8513d`) did not contain `smoke.py` yet, because I had not committed it. The UI shows that ref, and neither the trace panel nor the API response marks the code as uncommitted.

**Source location is the call site (lead D)**
- Cloud: `ask` is defined on line 12, but the trace says line 18, where it is called.
- Local test: `grep` and `read_file`, called from one dispatcher, both get the dispatcher's line.
- Local test: an async tool run with `asyncio.create_task` gets `_run`, line 88, inside Python's asyncio code.
- Why it may matter: the root cause prompt tells the agent to read the source at that file and line.
- UI source: file and line are shown only when a span fails, so a wrong location would show up exactly when someone is debugging.
- Not sure yet: the SDK comment says "first frame outside SDK internals", so the call site may be intended.

**Install size**
- `uv add traceroot openai python-dotenv` gave a 41 MB environment, including 15 OpenInference packages for frameworks and providers I do not use.

## Open questions (my answers)
Predictions come from the UI source on `main` at `7f600b2`. The cloud may run a different version, so I only tick a box after I see it.

- [x] Did the "Waiting for your first trace" page update by itself, and how long did it take?
  - Source: not checked for the onboarding page. The traces page asks every 3 s until a first trace exists.
  - What I saw: yes, it updated by itself. I did not time it.
- [ ] In the UI, does `first-trace` show or link to `smoke.py:18`?
  - Source: no. File and line only appear in the error box of a failed span, as plain text with no link. `first-trace` succeeded, so it should show nothing.
  - What I saw (UI v1.3.10): the trace row shows a repo link and a commit link (`ca8513d`), and no file or line. The UI source confirms both chips are GitHub links, shown only on the trace row. I have not clicked the agent span (second row) yet, and that is where a source location would be.
- [x] How does the UI show the missing cost?
  - Source: "-" in the trace list, and no cost chip on the model span.
  - What I saw: no cost anywhere in the trace tree or the trace header, only latency and tokens (35 in, 9 out, 44 total). The list's cost column was out of view.
- [ ] First impression: was it easy to find the trace and understand it?
  - What I saw:

## 2026-11-24: AI chat panel (Cloud, UI v1.3.10)
I opened the chat on my first trace and typed "nothing". It used one of the free chat runs.

- **Visible backticks (lead E).** The trace ID shows with literal backticks around it, inside the gray code style. In the source, the chat uses Tailwind's `prose` class, which adds backticks to inline code by default, and the inline `code` style in `message-list.tsx` does not turn that off. No existing report found.
- **Token line does not add up (lead F).** It shows "2 in, 191 out, 29,055 session, $0.1852" on the first message. "in" is labeled "Input tokens" and "session" is labeled "Cumulative session tokens". My guess: "in" leaves out cached input. 28,862 cache write tokens at $6.25 per million, plus 191 out at $25, comes to $0.1852, which matches. Not confirmed.

## Ollama, not TraceRoot
- The default `qwen2.5:3b-instruct` cut a 7,208 token prompt to 2,050 with no error. Fixed with `num_ctx 16384`.
- To check later: would a trace make that cut visible? Compare the input text with the prompt token count.
