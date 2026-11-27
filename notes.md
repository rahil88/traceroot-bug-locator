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
- Local test with failing async tools: `asyncio.run(agent())`, `create_task` and `gather` all record `asyncio/events.py:88` `_run`. Only a plain `await` records my own file.
- Local test: that path is absolute (`/Users/<name>/.../asyncio/events.py`), so it also sends my macOS username.
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
- [x] In the UI, does `first-trace` show or link to `smoke.py:18`?
  - Source: no. File and line only appear in the error box of a failed span, as plain text with no link. `first-trace` succeeded, so it should show nothing.
  - What I saw (UI v1.3.10): the trace row shows a repo link and a commit link (`ca8513d`), and no file or line. The UI source confirms both chips are GitHub links, shown only on the trace row. The agent span (second row) shows kind, latency, input, output and metadata (SDK name and version), and no file, line or git info. So the source location is stored (the API returns it) but not shown for a successful span, as predicted.
- [x] How does the UI show the missing cost?
  - Source: "-" in the trace list, and no cost chip on the model span.
  - What I saw: no cost anywhere in the trace tree or the trace header, only latency and tokens (35 in, 9 out, 44 total). The list's cost column was out of view.
- [x] First impression: was it easy to find the trace and understand it?
  - What I saw: easy to find your first trace

## 2026-11-24: AI chat panel (Cloud, UI v1.3.10)
I opened the chat on my first trace and typed "nothing". It used one of the free chat runs.

- **Visible backticks (lead E).** The trace ID shows with literal backticks around it, inside the gray code style. In the source, the chat uses Tailwind's `prose` class, which adds backticks to inline code by default, and the inline `code` style in `message-list.tsx` does not turn that off. No existing report found.
- **Token line does not add up (lead F).** It shows "2 in, 191 out, 29,055 session, $0.1852" on the first message. "in" is labeled "Input tokens" and "session" is labeled "Cumulative session tokens". My guess: "in" leaves out cached input. 28,862 cache write tokens at $6.25 per million, plus 191 out at $25, comes to $0.1852, which matches. Not confirmed.

## 2026-11-24: lead D reproduced (Cloud, `repro_d.py`, commit `5ef5e2e`, about 21:01 PST)

| Span | Defined at | Recorded | Seen in |
|---|---|---|---|
| `tool-create-task` | `repro_d.py:18` | `.../asyncio/events.py:88` `_run`, absolute path | UI error box and API |
| `repro-d` (agent) | `repro_d.py:38` | `.../asyncio/events.py:88` `_run` | API |
| `tool-await` | `repro_d.py:23` | `repro_d.py:44` | API |
| `tool-dispatch-a` | `repro_d.py:28` | `repro_d.py:49` | UI error box and API |
| `tool-dispatch-b` | `repro_d.py:33` | `repro_d.py:49` | API |

- `tool-gather` (added in `1918a30`): `events.py:88` in the UI error box, seen by me.
- Filed 2026-11-24: https://github.com/traceroot-ai/traceroot-py/issues/248
- **Claim:** async functions started by the event loop record Python's asyncio file instead of my code.
- **Do not claim:** that recording the call site is wrong. traceroot #1027 says that is intended, so the dispatcher rows are by design.
- Local test: skipping standard library frames fixes `asyncio.run`. For `create_task` it records the `asyncio.run` line, so it is only a partial fix.

## 2026-11-25: first traced agent runs (Cloud, issue 1218, commit `dbee46e`)

| | 3B | 4B |
|---|---|---|
| Result | no answer, 12 calls, `stop:max_calls` | correct file, 9 calls |
| Time | 14 s | 2 min 4 s (82 s and 8 calls on 2026-11-24) |
| Tokens | 5.0K in, 319 out | 20.1K in, 982 out |
| Failed tool calls | 2, every tool span OK | 1, every tool span OK |

Facts (UI screenshots and API):
- The tree shows each tool as `grep` or `read_file` with a time, so repeated searches only show when I open each span.
- Trace metadata arrived (stop, answer, calls, tool errors). The public API does not return tags, and `?tags=` is ignored.
- Same settings, different path: the 4B run is not fully repeatable at temperature 0 with a fixed seed.
- The 4B thinking text is stored in the model span output, but `reasoning_tokens` is 0, probably because Ollama does not report it.
- Minor: tool spans renamed with `update_current_span(name=...)` keep `call_tool` in `traceroot.span.path`. Not checked whether that matters.

What the 3B model asked for (model call spans, read through the API):

| Model call | Asked for |
|---|---|
| 1 | 4 calls at once: 2 searches and 2 reads of files that do not exist (`src/components/ModelSelector.js`) |
| 2 to 5 | the same 2 invented files again, swapping `onChange` and `value`, with a `path` argument grep does not have |

5 model calls made 12 tool calls. 10 of the 12 searches found nothing, but only 2 count as `tool_errors`, because "no matches" is not an error in my code.

My answers:
- [x] From the trace list alone, can I tell the 3B run failed?
  - "i cant see anything failing or being detected in 3b"
- [ ] How many clicks to see the 3B repeated the same searches?
- [ ] Can the UI filter the trace list by tag, for example `stop:max_calls`?
- [ ] Anything else confusing or missing:

## 2026-11-25: Task completion detector (Cloud)

Setup: template "Task completion" unchanged, default judge model, no filter, sampling 100%, root cause analysis Manual. Then I ran 1218 again on both models.

| Run | Flagged | Detector summary (from the findings API) |
|---|---|---|
| 3B, 15:58, `stop:max_calls` | Yes | "did not complete the file-identification request: it exhausted its tool calls searching nonexistent or unmatched paths and returned an empty answer" |
| 4B, 15:59, correct file | Yes | "identified the ModelSelector source file but did not include a regression-test file, and its proposed model-ID fallback would not preserve a model absent from the catalog" |

- The 3B catch is right, and its summary names the real cause.
- The 4B flag is not simply wrong. The issue's acceptance criteria say "Regression test covering this case", and the real fix (PR #1234) also added a new `model-selector.test.tsx`. My `answers.json` lists only the source file, because the candidate filter left test files out.
- The judge graded against the issue text, which is the root span's input. The agent's real job ("name 1 to 3 files to change") is only in the system prompt inside the model spans.
- The judge also read the 4B's reasoning and criticized the fix it had in mind.
- Each finding became its own signal: "Fails to provide the required file list after unsuccessful file search" and "Omits the required regression-test file from the proposed file list".
- Cost: 2 of 100 detector runs. No root cause analysis runs.

## 2026-11-25: task in the root span input (one variable)

Change: the `bug-locator` root span input now also holds the system prompt as `task` ("You find which source files must change to fix a bug ... call answer with 1 to 3 file paths"). Nothing else changed.

- 4B on 1218 (trace `e1a73d9d`, about 16:20): answered `frontend/ui/src/features/ai-assistant/components/model-selector.tsx`, correct for our task, 8 calls, 76 s.
- Detector: flagged again, about 60 s after the run. "The agent identified the ModelSelector implementation file but gave no regression-test file despite the acceptance criteria requiring a regression test, so the requested set of files is incomplete."
- Same verdict as the 15:59 run. Putting the task in the input did not change it: the judge still holds the agent to the issue's acceptance criteria.
- Cost: 1 more detector run (3 of 100 used).

## 2026-11-26: batch results and the detector check (Claude checked these through the API)

Scores (`uv run score.py results/*.jsonl`): keyword baseline 8/15, 3B 3/15, 4B 6/15. Both models score below the no-LLM baseline.
- Most failed runs never gave an answer: 12 for the 3B and 7 for the 4B. The answers they did give were mostly right: 3 of 3 for the 3B and 6 of 8 for the 4B.
- On 556, 557, 625 and 1244, the 3B made 0 tool calls and stopped.
- The 4B solved 1218, 3073 and 3075, which the baseline missed.

Detector against the scorer, 30 runs, sampling 100% (`uv run detector_check.py`, saved in `results/detector.jsonl`):

| Scorer | Runs | Flagged by detector |
|---|---|---|
| miss | 21 | 20 |
| hit | 9 | 3 |

The 4 disagreements, checked against the files in the real fix PRs:

| Run | Scorer | Detector | Who is right |
|---|---|---|---|
| 4B 625 | miss | not flagged | Detector. The answer was `.gitignore`, and PR #668 changed `.gitignore`. My answer key left that file out. |
| 3B 2030 | hit | "Includes unrelated files" | Detector, by a stricter rule: 2 of its 3 files are not in PR #2134 |
| 3B 1154 | hit | "Includes unrelated files" | Detector, by a stricter rule: 2 of its 3 files are not in PR #1155 |
| 4B 1154 | hit | "Omits a required implementation file" | Detector: PR #1155 changed `examples/python/claude-agent-sdk/main.py`, which the answer left out |

- **The answer key is too narrow.** It dropped test files, and also `.gitignore` and a new migration (625) and the example files and `pyproject.toml` (1154). Scored against every file in the real PRs, the 4B gets 7/15. The baseline and 3B stay the same.
- **The summaries match the raw traces where I checked.**
  - On 1567 the 3B wrote `answer([...])` as plain text instead of making a tool call.
  - On 1244 the 4B called `answer` with an empty list and got an error.
- **A summary can repeat the agent's wrong claim.** On 1244 the 4B reasoned that the fix is "in the agent repo (separate from this monorepo)", and the detector listed that as what the agent got right. The real fix is `frontend/packages/agent/src/tools/download-traces.ts`, which is in the same repo.
- **The same answer got different verdicts.** On 1218 the 4B answered `model-selector.tsx` in all 3 runs. The 15:59 and 16:20 runs were flagged for the missing regression test, but the batch run was not.
- **One signal mixes two failures.** The 23 findings are grouped into 7 signals. "Skips repository inspection and returns no required file list" holds both the 3B runs with 0 tool calls and the 4B runs on 556 and 557, which made 12 searches but read no file.
- **Cost:** 30 more detector runs, which should mean 33 of 100 used. Not yet checked in the UI.

## Ollama, not TraceRoot
- The default `qwen2.5:3b-instruct` cut a 7,208 token prompt to 2,050 with no error. Fixed with `num_ctx 16384`.
- To check later: would a trace make that cut visible? Compare the input text with the prompt token count.
