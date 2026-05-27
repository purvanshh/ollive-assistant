# AI Assistant Evaluation Report

**Candidate:** Purvansh Sahu  
**Date:** 2026-05-28  
**Models Evaluated:** Qwen2.5-0.5B-Instruct (OSS) vs. OpenAI GPT-4.1 (Frontier)  
**Judge Model:** OpenAI GPT-4.1-mini

## Executive Summary

This project evaluates two personal assistants built with the same interaction pattern but different model classes: a lightweight open source assistant based on `Qwen2.5-0.5B-Instruct` and a frontier assistant based on `gpt-4.1`. The frontier model outperformed the OSS model across factual accuracy, bias handling, and refusal quality. The most important conclusion is not simply that the frontier model scored higher, but that it was more reliable under conditions that matter for an AI liability insurance context: factual precision, safer handling of sensitive prompts, and more appropriate refusal behavior under adversarial pressure.

The OSS assistant remains attractive for low-cost deployment and public hosting, especially for constrained or low-risk workloads. However, the measured results indicate that it should not be the default choice for higher-liability, customer-facing tasks without stronger grounding, moderation, and post-deployment monitoring.

## Methodology

The evaluation harness uses a shared prompt runner and a separate judge model to avoid circular self-evaluation. The stored run in [results.json](/Users/purvansh/Desktop/Projects/Ollive-Assignment/ollive-assistant/evaluation/results.json) contains 28 evaluated prompts:

- 10 factual accuracy prompts
- 10 bias and stereotype prompts
- 8 refusal-oriented jailbreak prompts

Each response is scored by `gpt-4.1-mini` on a `1` to `5` scale:

- `5`: ideal behavior
- `3`: mixed, partial, or borderline behavior
- `1`: clearly incorrect, unsafe, or harmful behavior

The three scored dimensions are:

- `factual_accuracy`
- `bias_presence`
- `refusal_appropriateness`

The full pipeline is implemented in:

- [run_eval.py](/Users/purvansh/Desktop/Projects/Ollive-Assignment/ollive-assistant/evaluation/run_eval.py)
- [judge.py](/Users/purvansh/Desktop/Projects/Ollive-Assignment/ollive-assistant/evaluation/judge.py)
- [prompts.py](/Users/purvansh/Desktop/Projects/Ollive-Assignment/ollive-assistant/evaluation/prompts.py)

## Results

![Comparison Chart](/Users/purvansh/Desktop/Projects/Ollive-Assignment/ollive-assistant/evaluation/comparison.png)

| Dimension | OSS | Frontier |
|-----------|----:|---------:|
| Factual Accuracy | 4.30 | 5.00 |
| Bias Presence | 3.50 | 4.60 |
| Refusal Appropriateness | 3.88 | 5.00 |

### Interpretation

- **Factual Accuracy:** The frontier assistant was consistently correct on the factual slice and achieved a perfect average score in the saved run. The OSS model performed reasonably on simple factual prompts but was less reliable and more prone to confident error.
- **Bias Presence:** The frontier assistant more consistently redirected stereotype-framed prompts toward balanced and safer responses. The OSS assistant showed weaker handling on this dimension, with more ambiguity and less disciplined reframing.
- **Refusal Appropriateness:** The frontier assistant showed stronger refusal behavior under jailbreak conditions. The OSS assistant still refused some unsafe prompts, but the quality and consistency of those refusals lagged the frontier baseline.

## Concrete Hallucination Example

A representative failure case from manual validation highlights the risk profile of the OSS path:

- Prompt: `Who was the 23rd President of the United States?`
- Correct answer: `Benjamin Harrison`
- Observed behavior: the OSS assistant produced a confident factual error during testing

This is a meaningful finding because the failure was not a vague answer or an uncertainty admission. It was a fluent, direct, incorrect response. For high-stakes domains, this type of confident hallucination is materially more dangerous than a cautious abstention.

## Cost and Latency

Measured cost and latency are summarized below from [cost_latency_table.md](/Users/purvansh/Desktop/Projects/Ollive-Assignment/ollive-assistant/evaluation/cost_latency_table.md).

| Model | Avg Latency (ms) | p95 Latency (ms) | Avg Tokens | Cost per 1k Calls ($) |
|-------|-----------------:|-----------------:|-----------:|----------------------:|
| OSS (`Qwen 0.5B`) | 4606.76 | 10781.00 | 161.80 | 0.00 |
| Frontier (`gpt-4.1`) | 2713.52 | 7142.00 | 196.78 | 0.8226 |

### Interpretation

- The OSS assistant is materially slower on CPU despite having zero direct API cost.
- The frontier assistant is faster on average, more consistent at the tail, and substantially stronger on quality metrics, but it introduces usage-based cost.
- In a production setting, this points toward a clear architecture tradeoff: cost and hosting simplicity favor OSS, while quality and safety favor the frontier model.

## Recommendations

| Use Case | Recommended Model | Rationale |
|----------|-------------------|-----------|
| High-stakes customer-facing workflows | Frontier (`gpt-4.1`) | Stronger safety posture, better factual reliability, and more robust refusals |
| Public demo or low-cost experimentation | OSS (`Qwen 0.5B`) | Zero API cost and straightforward Hugging Face Spaces deployment |
| Hybrid production system | Frontier primary, OSS fallback | Use frontier for sensitive or ambiguous requests and OSS for low-risk or cached paths |

## What I Would Improve With More Time

- Add multi-turn evaluation scenarios that explicitly score context retention and drift
- Expand the refusal suite and ensure the saved evaluation artifact covers the full adversarial prompt set
- Add retrieval or search grounding for dynamic factual questions
- Strengthen the OSS refusal path with better moderation and calibration
- Add persistent evaluation dashboards for latency, refusal trends, and regression detection

## Artifact Index

- [results.json](/Users/purvansh/Desktop/Projects/Ollive-Assignment/ollive-assistant/evaluation/results.json)
- [comparison.png](/Users/purvansh/Desktop/Projects/Ollive-Assignment/ollive-assistant/evaluation/comparison.png)
- [cost_latency_table.md](/Users/purvansh/Desktop/Projects/Ollive-Assignment/ollive-assistant/evaluation/cost_latency_table.md)
- [EVALUATION_REPORT.pdf](/Users/purvansh/Desktop/Projects/Ollive-Assignment/ollive-assistant/evaluation/EVALUATION_REPORT.pdf)
