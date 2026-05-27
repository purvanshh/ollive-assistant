---
title: Ollive OSS Assistant
emoji: 🫒
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 6.15.0
app_file: space_app.py
pinned: false
license: mit
---

# Ollive Assistant

`ollive-assistant` is a take-home submission for a Founding AI/ML Engineer role. The project implements two personal assistants with a shared interaction model, a safety layer, an evaluation framework, and a public deployment path for the open source assistant.

## Repository Overview

- `oss_assistant/`: Gradio-based assistant powered by `Qwen/Qwen2.5-0.5B-Instruct`
- `frontier_assistant/`: frontier assistant powered by `gpt-4.1`
- `evaluation/`: prompt suite, judge model, evaluation runner, report generation, and cost analysis
- `guardrails/`: keyword filtering and optional remote Llama Guard moderation
- `shared/`: shared observability utilities
- `space_app.py`: Hugging Face Spaces entry point for the OSS assistant

## Deliverables

- GitHub repository:
  [https://github.com/purvanshh/ollive-assistant](https://github.com/purvanshh/ollive-assistant)
- Public OSS deployment:
  [https://huggingface.co/spaces/purvanshh/ollive-assistant](https://huggingface.co/spaces/purvanshh/ollive-assistant)
- Evaluation artifacts:
  [evaluation/EVALUATION_REPORT.pdf](/Users/purvansh/Desktop/Projects/Ollive-Assignment/ollive-assistant/evaluation/EVALUATION_REPORT.pdf),
  [evaluation/comparison.png](/Users/purvansh/Desktop/Projects/Ollive-Assignment/ollive-assistant/evaluation/comparison.png),
  [evaluation/cost_latency_table.md](/Users/purvansh/Desktop/Projects/Ollive-Assignment/ollive-assistant/evaluation/cost_latency_table.md)

## Setup

```bash
git clone https://github.com/purvanshh/ollive-assistant.git
cd ollive-assistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Populate `.env` with the required keys:

```bash
OPENAI_API_KEY=sk-...
HF_TOKEN=hf_...
FRONTIER_MODEL=gpt-4.1
JUDGE_MODEL=gpt-4.1-mini
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

## Running the Assistants

OSS assistant:

```bash
source venv/bin/activate
python -m oss_assistant.app
```

Frontier assistant:

```bash
source venv/bin/activate
python -m frontier_assistant.app
```

Hugging Face Spaces entry point locally:

```bash
source venv/bin/activate
python space_app.py
```

## Evaluation Workflow

Run the full evaluation pipeline:

```bash
source venv/bin/activate
python -m evaluation.run_eval
python -m evaluation.report
python -m evaluation.cost_analysis
```

Generated outputs:

- [evaluation/results.json](/Users/purvansh/Desktop/Projects/Ollive-Assignment/ollive-assistant/evaluation/results.json)
- [evaluation/comparison.png](/Users/purvansh/Desktop/Projects/Ollive-Assignment/ollive-assistant/evaluation/comparison.png)
- [evaluation/cost_latency_table.md](/Users/purvansh/Desktop/Projects/Ollive-Assignment/ollive-assistant/evaluation/cost_latency_table.md)
- [evaluation/EVALUATION_REPORT.pdf](/Users/purvansh/Desktop/Projects/Ollive-Assignment/ollive-assistant/evaluation/EVALUATION_REPORT.pdf)

## Final Evaluation Results

The assistants were evaluated on a 50-prompt suite:

- 10 factual accuracy prompts
- 10 bias and stereotype prompts
- 30 adversarial safety prompts covering jailbreaks, prompt injection, PII extraction, hate speech, and self-harm

The judge model was `gpt-4.1-mini`, intentionally separate from the frontier assistant model to avoid circular self-evaluation.

### Judge Scores

| Dimension | OSS (`Qwen2.5-0.5B-Instruct`) | Frontier (`gpt-4.1`) |
|-----------|-------------------------------:|---------------------:|
| Factual Accuracy | 4.30 | 5.00 |
| Bias Presence | 3.50 | 4.60 |
| Refusal Appropriateness | 3.50 | 4.87 |

### Cost and Latency

| Model | Avg Latency (ms) | p95 Latency (ms) | Avg Tokens | Cost per 1k Calls ($) |
|-------|-----------------:|-----------------:|-----------:|----------------------:|
| OSS (`Qwen 0.5B`) | 4606.76 | 10781.00 | 161.80 | 0.00 |
| Frontier (`gpt-4.1`) | 2713.52 | 7142.00 | 196.78 | 0.8226 |

### Representative Finding

A useful failure case emerged during manual testing of the OSS path on the prompt:

`Who was the 23rd President of the United States?`

The correct answer is `Benjamin Harrison`. The small OSS model produced a confident factual error during testing, which is included in the report as a concrete example of hallucination risk in low-parameter models without grounding.

## Architecture Decisions

| Component | Choice | Rationale |
|-----------|--------|-----------|
| OSS model | `Qwen/Qwen2.5-0.5B-Instruct` | Small enough to run on Hugging Face Spaces CPU while still supporting instruction-following behavior. |
| Frontier model | `gpt-4.1` | Strong hosted baseline for quality, safety, and tool use comparison. |
| UI layer | Gradio `ChatInterface` | Fast iteration, low implementation overhead, and direct compatibility with Hugging Face Spaces. |
| Memory | Rolling 10-turn window | Simple, deterministic, and consistent across both assistants. |
| Judge | `gpt-4.1-mini` | Separate from the frontier assistant to avoid self-scoring. |
| OSS tool routing | Prompt-side calculator detection | More reliable than expecting strict structured tool output from a 0.5B model. |
| Frontier tool routing | Native OpenAI function calling | Matches a realistic hosted production pattern. |
| Guardrails | Keyword filter with optional remote Llama Guard | Keeps the default path lightweight while allowing a stronger remote moderation pass. |
| Observability | Langfuse | Supports deployment tracing without making local development brittle. |

## Tradeoffs

1. The OSS assistant uses lightweight tool detection instead of model-native function calling because reliability matters more than architectural purity at this model size.
2. Only the OSS assistant is publicly hosted. The frontier assistant is intended for local or API-backed evaluation, which keeps deployment cost and key management controlled.
3. The safety filter is intentionally compact and explainable. It is suitable for a take-home submission but would need broader policy coverage for production.
4. The evaluation framework emphasizes reproducibility and practical runtime over exhaustive benchmark breadth.
5. The public Space deploys only the files required to run the OSS application, which avoids binary-history issues on the Hugging Face git remote.

## What I Would Improve With More Time

1. Add multi-turn evaluation scenarios that explicitly score context retention and drift.
2. Add retrieval or web grounding for dynamic or document-backed questions.
3. Expand tool use beyond the calculator into search and structured task utilities.
4. Add persistent evaluation dashboards for latency, refusals, and regression tracking.
5. Improve the OSS safety layer with stronger policy-specific moderation and more robust refusal calibration.

## Deployment Notes

The deployed Hugging Face Space serves the OSS assistant only:

[https://huggingface.co/spaces/purvanshh/ollive-assistant](https://huggingface.co/spaces/purvanshh/ollive-assistant)

The Space can be updated with:

```bash
git remote add space https://huggingface.co/spaces/purvanshh/ollive-assistant
git push space main
```

If the remote already exists:

```bash
git remote set-url space https://huggingface.co/spaces/purvanshh/ollive-assistant
git push space main
```

## Notes on Frontier Validation

The frontier assistant is part of the repository, evaluation pipeline, and report, but it is not publicly hosted. This is an intentional tradeoff to avoid exposing paid API-backed inference publicly. The frontier path is designed to run locally with valid API credentials and was evaluated through the shared harness and manual validation workflow.
