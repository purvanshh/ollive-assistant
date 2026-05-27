---
title: Ollive OSS Assistant
emoji: "🫒"
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 6.15.0
app_file: space_app.py
pinned: false
license: mit
---

# Ollive Assistant

Full-stack ML engineering take-home for a Founding AI/ML Engineer role. The
repo compares an open-source personal assistant against a frontier assistant,
then evaluates them on factual accuracy, bias safety, and refusal behavior.

## Quick Start

```bash
git clone https://github.com/purvanshh/ollive-assistant.git
cd ollive-assistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Populate `.env` with your OpenAI, Hugging Face, and optional Langfuse keys.

## Run The Apps

```bash
python -m oss_assistant.app
python -m frontier_assistant.app
python space_app.py
```

`oss_assistant.app.build_app()` is a valid Gradio `ChatInterface` constructor and
is used directly by `space_app.py` for Hugging Face Spaces deployment.

## Run Evaluation

```bash
python -m evaluation.run_eval
python -m evaluation.report
python -m evaluation.cost_analysis
```

## Architecture Decisions

| Component | Choice | Why |
|-----------|--------|-----|
| OSS model | `Qwen/Qwen2.5-0.5B-Instruct` | Small enough for Hugging Face Spaces free-tier CPU deployment while still supporting instruction following. |
| Frontier model | `gpt-4.1` | Strong hosted baseline for capability comparison and dependable tool calling. |
| UI | Gradio `ChatInterface` | Minimal surface area, fast iteration, and direct Hugging Face Spaces compatibility. |
| Memory | Rolling 10-turn window | Deterministic, simple to reason about, and keeps context bounded for both assistants. |
| Judge | Separate OpenAI judge model (`gpt-4.1-mini` by default) | Keeps the frontier model from grading itself and avoids circular evaluation. |
| OSS tools | Regex intent routing | More reliable than trying to force a 0.5B model into structured tool calls. |
| Frontier tools | OpenAI function calling | Native tool support gives a realistic production pattern for hosted models. |
| Guardrails | Keyword filter + optional Hugging Face Llama Guard | Fast first-pass blocking with a lightweight remote second pass when enabled. |
| Observability | Langfuse | Optional locally, but deployment-ready for hosted tracing in Spaces. |

## Tradeoffs Made

1. The OSS assistant uses prompt-side tool detection rather than model-native function calls because small local models are brittle at JSON/tool protocol adherence.
2. The evaluation harness is intentionally lightweight and CPU-friendly, which keeps it practical for take-home grading but leaves room for richer multi-turn benchmarks.
3. The Hugging Face Space only hosts the OSS path; the frontier model remains API-backed to keep hosted cost and complexity low.
4. The guardrail blocklist is intentionally compact and explainable, trading completeness for clarity and free-tier deployability.
5. Latency and token instrumentation are recorded at runtime so cost analysis can use real measurements instead of pure heuristics.

## What I Would Improve With More Time

1. Add persistent long-term memory with retrieval rather than limiting context to 10 turns.
2. Replace the OSS regex calculator trigger with a broader tool router and structured output fine-tuning.
3. Add retrieval or web search grounding for recent-event and document-based questions.
4. Expand evaluation to multi-turn scenarios, human spot checks, and longitudinal regression tracking.
5. Add stronger safety instrumentation such as policy-specific refusal dashboards and moderation analytics.

## Project Layout

```text
ollive-assistant/
├── oss_assistant/
├── frontier_assistant/
├── evaluation/
├── guardrails/
├── shared/
├── space_app.py
├── requirements.txt
└── README.md
```

## Environment Variables

```bash
OPENAI_API_KEY=sk-...
HF_TOKEN=hf_...
FRONTIER_MODEL=gpt-4.1
JUDGE_MODEL=gpt-4.1-mini
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

## Deploy To Hugging Face Spaces

Space URL:
[https://huggingface.co/spaces/purvanshh/ollive-assistant](https://huggingface.co/spaces/purvanshh/ollive-assistant)

Exact push commands:

```bash
git remote add space https://huggingface.co/spaces/purvanshh/ollive-assistant
git push space main
```

If the `space` remote already exists:

```bash
git remote set-url space https://huggingface.co/spaces/purvanshh/ollive-assistant
git push space main
```
