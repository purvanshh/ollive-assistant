# ADR 003: Blind Judge Evaluation Protocol

**Status:** Accepted
**Date:** 2026-06-16
**Deciders:** Ollive engineering team

## Context

Ollive's evaluation suite compares responses from two models (OSS and Frontier) across 200 prompts in 6 dimensions. The judge must be impartial — it must not know which model produced which response, preventing brand bias toward known frontier models.

## Decision

We implement a **strictly blind A/B comparison** using GPT-4.1 (or 4.1-mini with `--fast` flag) as the judge model.

### Protocol

1. Both models generate responses for the same prompt
2. Responses are randomized (Model A / Model B labeling is arbitrary)
3. Judge receives: prompt + Response A + Response B (no model identifiers)
4. Judge outputs: `Winner: <A/B/Tie>` + `Reasoning: <explanation>`
5. Per-dimension scores (1-5) are collected independently for each response
6. Judge responses are cached by `(prompt, response_pair)` hash to reduce API costs on re-runs

### Consistency Validation

- Target: judge scores within ±0.2 across three runs of the same prompt pair
- If deviation > 0.3 → flag for manual review
- Temperature set to 0.0 for deterministic scoring

## Consequences

### Positive
- Eliminates GPT-4.1's known bias toward its own outputs
- Dimension-level scoring enables fine-grained model comparison
- Caching reduces evaluation costs by ~60% on re-runs
- Consistent scores enable CI regression detection

### Negative
- GPT-4.1 judge costs ~$0.50-2.00 per full 200-prompt suite
- Judge itself may have biases toward certain response styles (verbosity, formatting)
- Does not evaluate multimodal responses
- Scoring rubrics may need refinement for edge cases

## Alternatives Considered

1. **Human evaluation:** Gold standard but impractical at scale (200 prompts × 5 raters = 1000 reviews).
2. **BERTScore/BLEU/ROUGE:** Automated metrics don't capture safety, bias, or factual accuracy. Rejected.
3. **Claude as judge:** Anthropic model could introduce different biases. Chose GPT-4.1 for cost/consistency balance.
4. **Self-evaluation (model judges itself):** Prone to self-preference. Rejected.
