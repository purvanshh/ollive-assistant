# Ollive Assistant

Full-stack ML engineering take-home for a Founding AI/ML Engineer role. The
repo compares an open-source personal assistant against a frontier assistant,
then evaluates them on factuality, bias, and jailbreak resistance.

## Quick Start

```bash
git clone <repo-url>
cd ollive-assistant
pip install -r requirements.txt
cp .env.example .env
```

Populate `.env` with your `OPENAI_API_KEY` and `HF_TOKEN`. Langfuse keys are
optional and only needed if you want observability traces.

## Run The Apps

```bash
python -m oss_assistant.app
python -m frontier_assistant.app
python space_app.py
```

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
| Frontier model | `gpt-4.1` | Strong baseline for capability comparison and dependable tool calling. |
| UI | Gradio `ChatInterface` | Minimal surface area, fast iteration, and direct Hugging Face Spaces compatibility. |
| Memory | Rolling 10-turn window | Deterministic, simple to reason about, and keeps context bounded for both assistants. |
| Judge | OpenAI rubric-based judge | Reuses the same provider as the frontier assistant and keeps operational setup simpler. |
| OSS tools | Regex intent routing | More reliable than trying to force a 0.5B model into structured tool calls. |
| Frontier tools | OpenAI function calling | Native tool support gives a realistic production pattern for hosted models. |
| Guardrails | Keyword filter + optional Llama Guard | Fast first-pass blocking with an optional second pass when you want deeper screening. |
| Observability | Optional Langfuse | Production-friendly tracing without making local development brittle. |

## Tradeoffs Made

1. The OSS assistant uses prompt-side tool detection rather than model-native function calls because small local models are brittle at JSON/tool protocol adherence.
2. The evaluation harness is single-turn and intentionally lightweight; that keeps grading fast but does not fully test long conversational drift.
3. The safety layer currently focuses on a compact blocklist plus optional external classification rather than a more comprehensive policy engine.
4. Token cost analysis uses a word-based heuristic instead of exact tokenizer accounting so it stays dependency-light and model-agnostic.
5. Hugging Face Spaces deployment targets the OSS assistant only, which is the right public demo surface but not a full hosted comparison environment.

## What I Would Improve With More Time

1. Add persistent long-term memory with retrieval rather than limiting context to 10 turns.
2. Replace the OSS regex calculator trigger with a more general tool router and structured outputs fine-tuning.
3. Add web search or document retrieval so both assistants can ground answers on recent or user-provided data.
4. Expand evaluation to multi-turn scenarios, latency percentiles, and human spot-checking.
5. Add stronger safety instrumentation such as policy-specific refusal tests and audit dashboards.

## Project Layout

```text
ollive-assistant/
├── oss_assistant/
├── frontier_assistant/
├── evaluation/
├── guardrails/
├── shared/
├── space_app.py
├── space_README.md
├── requirements.txt
└── README.md
```

## Environment Variables

```bash
OPENAI_API_KEY=sk-...
HF_TOKEN=hf_...
FRONTIER_MODEL=gpt-4.1
JUDGE_MODEL=gpt-4.1
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
```

## Deployment

Use `space_app.py` as the Hugging Face Spaces entry point for the OSS assistant.

Public Spaces URL placeholder:
`https://huggingface.co/spaces/<your-username>/ollive-assistant`
