# TraceRoot side quest: bug locator (plan, 2026-11-24, in progress)

Goal: a small Python agent that reads a closed TraceRoot issue, searches the pre-fix code and names the files to fix. Score against the real PR. Trace every run with TraceRoot.
Rules: I build it, Claude guides and reviews. $0 spend, local Qwen only. Only claim what I reproduced. New code only, no existing projects.
Out of scope: fixing bugs, a UI, multi-agent, comments posted by the agent on their repo.

## Day 1: build (about 6 h)
- [x] 1. `git init` here, push to a new GitHub repo, `.env` in `.gitignore` (15 min)
- [x] 2. Give Ollama a bigger context: default is 4096. Use `models/*.Modelfile` with `num_ctx 16384`, confirm with `ollama ps` (15 min)
  - [x] `qwen2.5-3b-16k`: `ollama ps` shows 16384. Long prompt test: default kept 2,050 of 7,208 tokens with no error and missed the fact, 16k found it
  - [x] `qwen3.5-4b-16k`: `ollama ps` shows 16384. It runs on MLX, where the default kept all 7,190 tokens, so it does not cut the prompt the same way
  - Watch: one model loaded at a time (`ollama stop <model>`), 16 GB RAM was swapping. Set temperature 0 on both, the 4B defaults to 1
- [ ] 3. TraceRoot cloud account, API key, one traced call. Write friction in `notes.md` as it happens (1 h)
  - [x] account, key, project `bug-locator`, first trace arrived (checked through the API: 2 spans, 35 in, 9 out)
  - [x] `notes.md` started (Claude drafted from recorded facts)
  - [ ] I check the trace in the UI and fill in the open questions in `notes.md`
- [ ] 4. Hand-pick 15 issues from `tasks/candidates.md`, real bugs only (about 20 of the 46 look like bugs by title). Export each pre-fix tree with `git archive`, so there is no `.git` to leak the fix (1 h)
- [ ] 5. Three tools: `grep`, `read_file`, `answer` (max 3 paths). Cap output, block paths outside the tree, return errors as text (1 h)
- [ ] 6. Agent loop: max 12 tool calls, stop on `answer`. One issue working end to end (1.5 h)
- [ ] 7. Tracing: `Integration.OPENAI`, `@observe` on loop and tools, tags for issue, model and outcome (45 min)
  - Checkpoint: one full trace in the UI, tree matches what the agent did

## Day 2: measure and report (about 6 h)
- [ ] 8. Scorer: hit if any of 3 paths is in the real fix. Plus a no-LLM keyword grep baseline (45 min)
- [ ] 9. Run 15 issues on `qwen2.5-3b-16k`, then `qwen3.5-4b-16k`. Qwen only, no cloud models (1.5 h)
- [ ] 10. Read 10 failed traces. Label each: bad search, loop, invented path, opened then dropped, context overflow, gave up (1 h)
- [ ] 11. Reproduce leads A, B, C in the cloud UI, plus anything in `notes.md` (1 h)
- [ ] 12. Search duplicates again, file one issue with a minimal repro (45 min)
- [ ] 13. README with results table and limits, then the application paragraph (1 h)
- [ ] Stretch: PR for lead B, or rerun as a TraceRoot eval

## Leads to reproduce (found in a local probe, SDK 0.5.1)
- A: `@observe` async tool cancelled by `asyncio.wait_for` is stored OK, no output
- B: failed OpenAI chat call is stored with no model (Anthropic keeps it)
- C: streamed call without usage is over-counted ("Hi": 86 output tokens stored, 2 real)
- D: `@observe` records where a function is called, not where it is defined. Tools called from one dispatcher all get the dispatcher line, and an async tool run with `asyncio.create_task` gets Python's `_run`. Their RCA prompt tells the agent to read that source. First sighting in my cloud trace: `smoke.py:18 <module>`. No existing report found 2026-11-24. The UI shows the location only on failed spans, so reproduce it with an async tool that raises
- Skip, already reported: `whoami` http host (#2675), missing cost shown as 0 (#2736, PR #2740)

## Review
(fill in after)
