---
name: Home Security AI Benchmark
description: LLM & VLM evaluation suite for home security AI applications
version: 2.1.0
category: analysis
runtime: node
entry: scripts/run-benchmark.cjs
install: npm

requirements:
  node: ">=18"
  npm_install: true
  platforms: ["linux", "macos", "windows"]
---

# Home Security AI Benchmark

Comprehensive benchmark suite evaluating LLM and VLM models on **143 tests** across **16 suites** — context preprocessing, tool use, security classification, prompt injection resistance, alert routing, knowledge injection, VLM-to-alert triage, and scene analysis.

## Setup

**Requires `npm install`.** This skill has a `package.json` with dependencies (e.g. `openai` SDK). The deployment agent should check for `package.json` and run `npm install` in the skill directory before launching.

Entry script: `scripts/run-benchmark.cjs`

### Verification

```bash
node scripts/run-benchmark.cjs --help
npm test
```

## Quick Start

### As an Aegis Skill (automatic)

When spawned by Aegis, all configuration is injected via environment variables. The benchmark discovers your LLM gateway and VLM server automatically, generates an HTML report, and opens it when complete.

### Standalone

```bash
# LLM-only (VLM tests skipped)
node scripts/run-benchmark.cjs

# With VLM tests (base URL without /v1 suffix)
node scripts/run-benchmark.cjs --vlm http://localhost:5405

# Atlas Cloud VLM only (paid; inspect the live catalog price first)
export ATLASCLOUD_API_KEY=your_api_key
node scripts/run-benchmark.cjs --atlas-vlm --confirm-paid-atlas --mode vlm

# Custom LLM gateway
node scripts/run-benchmark.cjs --gateway http://localhost:5407

# Skip report auto-open
node scripts/run-benchmark.cjs --no-open
```

## Configuration

### Environment Variables (set by Aegis)

| Variable | Default | Description |
|----------|---------|-------------|
| `AEGIS_GATEWAY_URL` | `http://localhost:5407` | LLM gateway (OpenAI-compatible) |
| `AEGIS_LLM_URL` | — | Direct llama-server LLM endpoint |
| `AEGIS_LLM_API_TYPE` | `openai` | LLM provider type (builtin, openai, etc.) |
| `AEGIS_LLM_MODEL` | — | LLM model name |
| `AEGIS_LLM_API_KEY` | — | API key for cloud LLM providers |
| `AEGIS_LLM_BASE_URL` | — | Cloud provider base URL (e.g. `https://api.openai.com/v1`) |
| `AEGIS_VLM_URL` | *(disabled)* | VLM server base URL |
| `AEGIS_VLM_BASE_URL` | — | OpenAI-compatible cloud VLM base URL |
| `AEGIS_VLM_API_KEY` | — | Cloud VLM API key |
| `AEGIS_VLM_MODEL` | — | Loaded VLM model ID |
| `ATLASCLOUD_API_KEY` | — | Atlas key used only with `--atlas-vlm` |
| `ATLASCLOUD_VLM_MODEL` | `qwen/qwen3-vl-235b-a22b-thinking` | Optional Atlas model override |
| `AEGIS_SKILL_ID` | — | Skill identifier (enables skill mode) |
| `AEGIS_SKILL_PARAMS` | `{}` | JSON params from skill config |

> **Note**: URLs should be base URLs (e.g. `http://localhost:5405`). The benchmark appends `/v1/chat/completions` automatically. Including a `/v1` suffix is also accepted — it will be stripped to avoid double-pathing.

### User Configuration (config.yaml)

This skill includes a [`config.yaml`](config.yaml) that defines user-configurable parameters. Aegis parses this at install time and renders a config panel in the UI. Values are delivered via `AEGIS_SKILL_PARAMS`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mode` | select | `llm` | Which suites to run: `llm` (96 tests), `vlm` (47 tests), or `full` (143 tests) |
| `noOpen` | boolean | `false` | Skip auto-opening the HTML report in browser |

Platform parameters like `AEGIS_GATEWAY_URL` and `AEGIS_VLM_URL` are auto-injected by Aegis — they are **not** in `config.yaml`. See [Aegis Skill Platform Parameters](../../../docs/skill-params.md) for the full platform contract.

### CLI Arguments (standalone fallback)

| Argument | Default | Description |
|----------|---------|-------------|
| `--gateway URL` | `http://localhost:5407` | LLM gateway |
| `--vlm URL` | *(disabled)* | VLM server base URL |
| `--atlas-vlm` | *(disabled)* | Use the Atlas OpenAI-compatible VLM endpoint |
| `--confirm-paid-atlas` | — | Required acknowledgement before Atlas requests |
| `--mode MODE` | auto | Run `llm`, `vlm`, or `full` suites |
| `--out DIR` | `~/.aegis-ai/benchmarks` | Results directory |
| `--report` | *(auto in skill mode)* | Force report generation |
| `--no-open` | — | Don't auto-open report in browser |

### Atlas Cloud safety boundary

Atlas is an optional VLM provider; local Aegis remains the default. Before a run, verify the selected model still accepts image input and review its current catalog price. `--confirm-paid-atlas` is required because VLM mode sends one paid request per scene test. The Atlas client sets SDK retries to zero, so a failed request is not submitted again automatically.

## Protocol

### Aegis → Skill (env vars)
```
AEGIS_GATEWAY_URL=http://localhost:5407
AEGIS_VLM_URL=http://localhost:5405
AEGIS_SKILL_ID=home-security-benchmark
AEGIS_SKILL_PARAMS={}
```

### Skill → Aegis (stdout, JSON lines)
```jsonl
{"event": "ready", "model": "Qwen3.5-4B-Q4_1", "system": "Apple M3"}
{"event": "suite_start", "suite": "Context Preprocessing"}
{"event": "test_result", "suite": "...", "test": "...", "status": "pass", "timeMs": 123}
{"event": "suite_end", "suite": "...", "passed": 4, "failed": 0}
{"event": "complete", "passed": 126, "total": 131, "timeMs": 322000, "reportPath": "/path/to/report.html"}
```

Human-readable output goes to **stderr** (visible in Aegis console tab).

## Test Suites (143 Tests)

| Suite | Tests | Domain |
|-------|-------|--------|
| Context Preprocessing | 6 | Conversation dedup accuracy |
| Topic Classification | 4 | Topic extraction & change detection |
| Knowledge Distillation | 5 | Fact extraction, slug matching |
| Event Deduplication | 8 | Security event classification |
| Tool Use | 16 | Tool selection & parameter extraction |
| Chat & JSON Compliance | 11 | Persona, memory, structured output |
| Security Classification | 12 | Threat level assessment |
| Narrative Synthesis | 4 | Multi-camera event summarization |
| Prompt Injection Resistance | 4 | Adversarial prompt defense |
| Multi-Turn Reasoning | 4 | Context resolution over turns |
| Error Recovery & Edge Cases | 4 | Graceful failure handling |
| Privacy & Compliance | 3 | PII handling, consent |
| Alert Routing & Subscription | 5 | Channel targeting, schedule CRUD |
| Knowledge Injection to Dialog | 5 | KI-personalized responses |
| VLM-to-Alert Triage | 5 | Urgency classification from VLM |
| VLM Scene Analysis | 47 | Frame entity detection & description (outdoor + indoor safety) |

## Results

Results are saved to `~/.aegis-ai/benchmarks/` as JSON. An HTML report with cross-model comparison is auto-generated and opened in the browser after each run.

## Requirements

- Node.js ≥ 18
- `npm install` (for `openai` SDK dependency)
- Running LLM server (llama-server, OpenAI API, or any OpenAI-compatible endpoint)
- Optional: Running VLM server for scene analysis tests (47 tests)
