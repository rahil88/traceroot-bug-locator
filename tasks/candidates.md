# Candidate issues (46, generated 2026-11-24)

Filter: closed, one merged PR in traceroot-ai/traceroot, 1 to 3 source files, issue text does not contain any fixed file name or stem.
Not hand-checked. More than half are feature requests or have docs-style fixes: drop those. The last column is the answer, so never show it to the agent.

| Created | Issue | PR | Pre-fix commit | Title | Fixed files |
|---|---|---|---|---|---|
| 2026-11-16 | #3076 | #3081 | `dbf261cad` | Copy buttons provide no feedback when clipboard access fails | frontend/ui/src/components/ui/copy-button.tsx |
| 2026-11-16 | #3075 | #3080 | `dbf0a501d` | Member dialogs retain old invitation errors and hide role-save failure | frontend/ui/src/features/settings/workspace/components/MembersTab.tsx |
| 2026-11-16 | #3073 | #3078 | `fec5fec00` | Settings field labels do not focus or identify their controls consiste | frontend/ui/src/features/settings/project/components/AccessKeysTab.tsx<br>frontend/ui/src/features/settings/workspace/components/MembersTab.tsx<br>frontend/ui/src/features/settings/workspace/components/ModelProvidersTab.tsx |
| 2026-10-22 | #2723 | #2724 | `721ef0d49` | Let the app report the dollar cost of an LLM call | backend/rest/services/trace_reader.py<br>backend/worker/otel_transform.py<br>frontend/ui/src/features/traces/utils/index.ts |
| 2026-10-16 | #2621 | #2653 | `08e231d75` | Update the BYOK model lists to the current provider models | frontend/packages/core/src/llm-providers.ts |
| 2026-09-24 | #2318 | #2469 | `907810103` | Generate the references and add parity tests so the docs can't drift | backend/rest/routers/public/traces_read.py |
| 2026-08-27 | #2030 | #2134 | `056a93d21` | Alerts: debounce entry into NO_DATA under noDataMode=NOTIFY | frontend/worker/src/alerts/scheduler.ts<br>frontend/worker/src/alerts/severity-state-machine.ts |
| 2026-07-30 | #1667 | #1776 | `904579340` | Scorers catalog + read-only detail (LLM judge vs code snippet, honest  | frontend/ui/src/features/evaluations/views/evaluations-view.tsx |
| 2026-07-30 | #1659 | #1757 | `568c67e5a` | Test-case table + slide-in per-case panel (editing publishes a new dat | frontend/ui/src/features/evaluations/views/dataset-detail-view.tsx<br>frontend/ui/src/features/offline-eval/components/test-case-review-drawer.tsx |
| 2026-07-30 | #1656 | #1777 | `4bdcd886a` | Derive per-result cost from the trace on ingest, scoped to the candida | frontend/ui/src/features/evaluations/views/compare-case-drawer.tsx<br>frontend/ui/src/features/evaluations/views/compare-runs-view.tsx |
| 2026-07-30 | #1644 | #1758 | `1de22e6ec` | `POST /evaluation-runs` — register a run, resolve the `(project, name) | frontend/ui/src/app/api/public/evaluation-runs/route.ts<br>frontend/ui/src/features/evaluations/views/dataset-detail-view.tsx<br>frontend/ui/src/features/offline-eval/components/test-case-review-drawer.tsx |
| 2026-07-15 | #1568 | #1570 | `b3a63ffdd` | Agent-side RCA failure is recorded as done with an empty result instea | frontend/worker/src/processors/detector-rca-processor.ts<br>frontend/worker/src/processors/detector-run-processor.ts |
| 2026-07-15 | #1567 | #1569 | `423d854c1` | Environment trigger conditions never match: ingest drops the environme | backend/db/clickhouse/client.py<br>backend/worker/otel_transform.py |
| 2026-07-07 | #1453 | #1516 | `d012ad405` | feat(ui): widget cards, chart renderers, and trace-feed/detector widge | frontend/ui/src/features/dashboards/components/DashboardGrid.tsx<br>frontend/ui/src/features/dashboards/components/WidgetCard.tsx |
| 2026-06-30 | #1399 | #1400 | `23f33cfdf` | Add support for Claude Sonnet 5 (claude-sonnet-5) | frontend/packages/core/src/llm-providers.ts |
| 2026-06-19 | #1247 | #1251 | `acc9b9f42` | Support GLM-5.2 | frontend/packages/core/src/llm-providers.ts |
| 2026-06-18 | #1244 | #1245 | `afecf289d` | Agent trace analysis sees empty per-span I/O (downloads skeleton, not  | frontend/packages/agent/src/tools/download-traces.ts |
| 2026-06-17 | #1224 | #1227 | `5bf64206b` | Clearing a BYOK provider's Base URL doesn't reset it — the stale custo | frontend/ui/src/features/settings/workspace/components/ModelProvidersTab.tsx |
| 2026-06-17 | #1218 | #1234 | `8ec7696a2` | Detector Agent Model reverts to the default model on refresh when the  | frontend/ui/src/features/ai-assistant/components/model-selector.tsx |
| 2026-06-15 | #1198 | #1203 | `6d49a41ba` | Page-number input in pagination can't be cleared (always keeps one dig | frontend/ui/src/components/list-pagination.tsx |
| 2026-06-11 | #1162 | #1165 | `4e2c70c50` | bug (ui): When trace details is expanded we have 2 agent bot button | frontend/ui/src/components/layout/app-layout.tsx |
| 2026-06-11 | #1154 | #1155 | `087f6b436` | claude-agent-sdk (python): keep traces sparse on ingest + refresh exam | backend/worker/otel_transform.py |
| 2026-06-05 | #1079 | #1097 | `c80d7b363` | Onboarding: surface Slack availability so users can connect during onb | frontend/ui/src/features/traces/components/GettingStarted/AITab.tsx<br>frontend/ui/src/features/traces/components/GettingStarted/ManualTab.tsx |
| 2026-06-03 | #1036 | #1073 | `3485fa491` | [OpenAPI] Publish public API schema artifact for CLI codegen | backend/rest/openapi_public.py |
| 2026-05-22 | #933 | #936 | `9768dad62` | [Docs] Add Pydantic AI to docs | frontend/ui/src/features/traces/components/GettingStarted/integrations.tsx |
| 2026-05-08 | #857 | #858 | `ac3d81047` | [Bug] Trace root duration shorter than child span duration in live/lon | frontend/ui/src/features/traces/utils/index.ts |
| 2026-04-25 | #756 | #757 | `e74f688cc` | feat: support DeepSeek V4 in BYOK API | frontend/packages/core/src/llm-providers.ts |
| 2026-04-21 | #706 | #714 | `d260e4b34` | [UI] In-progress spans/traces use italic style instead of grey backgro | frontend/ui/src/features/traces/components/SpanTreeView.tsx |
| 2026-04-16 | #689 | #691 | `2c832e0cc` | Support opus 4.7 in Traceroot | frontend/packages/core/src/llm-providers.ts |
| 2026-04-15 | #677 | #682 | `9e6b2467b` | [Docs] Add lambda index in the docs | frontend/ui/src/features/traces/components/GettingStarted/AITab.tsx<br>frontend/ui/src/features/traces/components/GettingStarted/ManualTab.tsx |
| 2026-04-15 | #676 | #682 | `9e6b2467b` | [UX] Add lambda index in the onboarding flow | frontend/ui/src/features/traces/components/GettingStarted/AITab.tsx<br>frontend/ui/src/features/traces/components/GettingStarted/ManualTab.tsx |
| 2026-04-14 | #675 | #685 | `7a39c5894` | [UX] Add CrewAI in the onboarding flow | frontend/ui/src/features/traces/components/GettingStarted/AITab.tsx<br>frontend/ui/src/features/traces/components/GettingStarted/ManualTab.tsx<br>frontend/ui/src/features/traces/components/GettingStarted/integrations.tsx |
| 2026-04-14 | #674 | #684 | `9e2e24c0f` | [UX] Add AutoGen in the onboarding flow | frontend/ui/src/features/traces/components/GettingStarted/AITab.tsx<br>frontend/ui/src/features/traces/components/GettingStarted/integrations.tsx |
| 2026-04-09 | #646 | #652 | `5e056b1e4` | [UX][Onboarding] Include github app installation in the onboarding pro | frontend/ui/src/features/traces/components/GettingStarted/AITab.tsx<br>frontend/ui/src/features/traces/components/GettingStarted/ManualTab.tsx |
| 2026-04-08 | #641 | #663 | `f5d518555` | [BYOK] Support latest GLM model | frontend/packages/core/src/llm-providers.ts |
| 2026-04-06 | #625 | #668 | `eb94bafd6` | bug: fresh make dev-lite / make prod-lite fails — no Prisma migrations | tmux_tools/launcher.py |
| 2026-03-30 | #578 | #593 | `339c26a10` | [UI] When the ai generated content is too wide, the display looks sket | frontend/ui/src/features/ai-assistant/components/message-list.tsx |
| 2026-03-23 | #557 | #577 | `739437afa` | Do not show agent chat button in all places | frontend/ui/src/components/layout/app-layout.tsx<br>frontend/ui/src/features/ai-assistant/components/ai-assistant-panel.tsx |
| 2026-03-23 | #556 | #564 | `6fd87153e` | Remove the delete self button | frontend/ui/src/features/settings/workspace/components/MembersTab.tsx |
| 2026-03-21 | #552 | #554 | `5a566b2b3` | For xAI, GLM and Kimi default model ids are not provided. | frontend/ui/src/features/settings/workspace/components/ModelProvidersTab.tsx |
| 2026-03-18 | #533 | #543 | `8a24f8485` | Support more BYOK models (xAI, Kimi2.5 and GLM5) | frontend/packages/core/src/llm-providers.ts<br>frontend/ui/src/app/api/workspaces/[workspaceId]/model-providers/route.ts |
| 2025-09-12 | #167 | #177 | `94c48b683` | [Token Refresh] Even after token refresh the original token is shown i | ui/src/components/integrate/Item.tsx |
| 2025-09-01 | #126 | #127 | `006871198` | Local mode logs by traceId not working | rest/client/jaeger_client.py |
| 2025-08-30 | #118 | #139 | `c0cd111c4` | [UI] The explainability could be hidden by the trace section | ui/src/components/right-panel/agent/ChatMessage.tsx |
| 2025-08-20 | #87 | #107 | `309d1bb6b` | [Enhancement][REST] Async in rest fastapi | rest/agent/agent.py<br>rest/client/github_client.py |
| 2025-08-20 | #75 | #101 | `d6628923e` | [BUG] `TRACE_ROOT_LOCAL_MODE` is misleading | rest/app.py<br>rest/routers/explore.py<br>rest/routers/integrate.py |
