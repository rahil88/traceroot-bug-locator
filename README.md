# traceroot-bug-locator

A small agent that reads a real bug report from [traceroot-ai/traceroot](https://github.com/traceroot-ai/traceroot) and names the 1 to 3 files that must change to fix it. It runs on local Qwen models through Ollama, and every run is traced with the TraceRoot Python SDK (0.5.1) into TraceRoot Cloud. I built it to use TraceRoot the way a user would, on a task where I know the right answer, and to write down what helped and what got in the way.

## Results

15 closed TraceRoot issues, each with the code as it was before the fix. A run is a hit if any file it names was changed by the real fix.

| Runner | Hits | Answered | Invented paths | Median time per issue |
|---|---|---|---|---|
| Keyword baseline (no LLM) | 8/15 | 15/15 | 0 | 0.3 s |
| qwen2.5 3B | 3/15 | 3/15 | 0 | 29 s |
| qwen3.5 4B | 6/15 (7/15) | 8/15 | 0 | 111 s |

- **Both models lost to a keyword search with no model at all.** I wrote the baseline before seeing any model scores and did not tune it or the agent's prompt afterwards.
- **When a model answered, it was usually right** (3B: 3 of 3, 4B: 6 of 8). Most failures never gave an answer.
- **The 4B solved 3 issues the baseline missed** (1218, 3073, 3075), so the two approaches miss different issues.
- **(7/15):** my answer key only lists source files. Scored against every file in the real PRs, the 4B's `.gitignore` answer on #625 is a hit. TraceRoot's detector caught this before I did (see below).

## Why the runs failed

20 failed runs, labeled by fixed rules from the run logs ([`analyze.py`](analyze.py)):

| Label | Runs | What it looks like |
|---|---|---|
| Opened then dropped | 6 | Read a file from the real fix, then never answered with it. Four of these are 4B runs that ran out of tool calls. |
| Gave up | 4 | The 3B made 0 tool calls and stopped. |
| Invented path | 3 | The 3B tried to read `.js` files that don't exist in a TypeScript repo. |
| Loop | 3 | The same call repeated 3 to 7 times. |
| Bad search | 3 | Searched and never found the right file. On #1244 the 4B decided the fix was in "a separate repo" and answered with an empty list. |
| Wrong file | 1 | Answered with files the fix did not touch. |

No run hit the context limit: the largest prompt was 11,145 of 16,384 tokens. For the 4B, the 12-call budget looks like a bigger limit than search: 4 of its 7 runs that ran out of calls had already opened a right file.

## What I found about TraceRoot

1. **Async source location bug, filed as [traceroot-py #248](https://github.com/traceroot-ai/traceroot-py/issues/248).** When an `@observe` function runs through `asyncio.run`, `create_task` or `gather`, the error box points to Python's own `asyncio/events.py:88` instead of my code, and the path is absolute, so it also sends the local username. A plain `await` is fine. [`repro_d.py`](repro_d.py) reproduces it.
2. **A run that never answers looks like a healthy run.** With no exception there is no error status, so the trace list shows the 3B's failed run the same as a successful one. To spot a failure I had to open the trace or use a detector. Tags (`stop:max_calls`) are on the trace, but the public API does not return them.
3. **The task completion detector agreed with my scorer on 26 of 30 runs, and was right about all 4 disagreements** ([`detector_check.py`](detector_check.py)). It flagged 20 of 21 misses. Each of its 4 disagreements is explained by the real fix PR: it passed the `.gitignore` answer my key had wrongly scored as a miss, and it flagged 3 hits that named unrelated files or left out a file the fix changed. Three weaker spots:
   - **Same answer, different verdict:** the 4B gave the same correct answer to #1218 in 3 runs. Two were flagged for a missing regression test and one was not.
   - **It can repeat the agent's wrong claim:** on #1244 it listed "the fix is in a separate repo" as something the agent got right. The file is in the same repo.
   - **One signal mixes two failures:** the 3B runs with 0 tool calls and the 4B runs that searched 12 times without opening a file both land under "Skips repository inspection".

## How it works

- [`prepare_data.py`](prepare_data.py) takes 15 issues, exports each pre-fix commit with `git archive` (no `.git`, so the fix can't leak), and records the source files the fix changed.
- [`tools.py`](tools.py) gives the agent `grep`, `read_file` and `answer` (1 to 3 paths), with capped output and no access outside the tree.
- [`agent.py`](agent.py) is the loop: at most 12 tool calls, temperature 0, seed 0. It is traced with `@observe` (agent span plus one span per tool) and `Integration.OPENAI` for the model calls.
- [`run_batch.py`](run_batch.py) runs one model on all 15 issues, saves after each issue, resumes if stopped, and puts each model in its own TraceRoot session.
- [`score.py`](score.py), [`baseline.py`](baseline.py), [`analyze.py`](analyze.py) and [`detector_check.py`](detector_check.py) produce the numbers above from `results/`.

## Limits

- 15 issues from one repo is a small sample. Two of them (1218, 3076) are easy.
- Runs are not fully repeatable: even at temperature 0 with a fixed seed, Ollama can give different outputs.
- A hit only needs one right file. It doesn't check that the list is complete.
- Only two small local models, chosen to stay on free tiers.
- The failure labels come from fixed rules over the run logs. I checked some of them by reading the traces in TraceRoot.

## Run it

```bash
uv sync
ollama create qwen2.5-3b-16k -f models/qwen2.5-3b-16k.Modelfile
ollama create qwen3.5-4b-16k -f models/qwen3.5-4b-16k.Modelfile
uv run prepare_data.py                 # needs a logged in gh
cp .env.example .env                   # add TRACEROOT_API_KEY
uv run run_batch.py qwen3.5-4b-16k
uv run score.py results/*.jsonl
uv run pytest
```

Raw observations as I went are in [`notes.md`](notes.md).
