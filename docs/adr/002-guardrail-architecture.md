# ADR 002: Guardrail Architecture

**Status:** Accepted
**Date:** 2026-06-16
**Deciders:** Ollive engineering team

## Context

As an AI gateway that routes prompts between local and cloud models, Ollive must prevent harmful content from reaching any model. The guardrail must operate locally (privacy-first) and introduce minimal latency (<300ms target).

## Decision

We use **Local Llama Guard 3 (1B)** as the primary safety filter, with a **keyword-based fallback** when the guard model is unavailable.

### Architecture

```
User Prompt → Llama Guard 3 (1B) → SAFE → Router → Model
                                  → UNSAFE → Refusal + Audit Log
```

### Taxonomy

The guardrail uses the MLCommons safety taxonomy:
- Violent Crimes (S1)
- Non-Violent Crimes (S2)
- Sex-Related Crimes (S3)
- Child Sexual Exploitation (S4)
- Defamation (S5)
- Specialized Advice (S6)
- Privacy (S7)
- Intellectual Property (S8)
- Indiscriminate Weapons (S9)
- Hate (S10)
- Suicide & Self-Harm (S11)
- Sexual Content (S12)
- Elections (S13)
- Code Generation Assistance (S14)

### Fallback

When Llama Guard is unavailable (cold start, Ollama down):
- Pattern-based keyword filter catches obvious jailbreaks
- Regex for PII, injection patterns
- Returns "Guardrail service unavailable" with safe-mode routing (OSS-only)

## Consequences

### Positive
- <300ms latency on CPU for 1B model
- All checks happen locally (no data leaves the server for safety checks)
- Detailed reason codes logged to `audit_logs` for transparency
- Benign queries pass with near-zero false positive rate

### Negative
- 1B model has ~85-90% recall (some harmful content may pass)
- Requires ~1GB RAM for Llama Guard model in memory
- Cold start adds 2-5s for model loading
- Does not cover multimodal content safety

## Alternatives Considered

1. **OpenAI Moderation API:** Higher accuracy but sends data to third-party. Violates local-first privacy principle.
2. **HuggingFace text-classification pipeline:** Simpler but less accurate for nuanced safety classification. Rejected.
3. **Llama Guard 3 (8B):** Higher accuracy but ~300-800ms latency on CPU. Exceeds latency budget.
4. **Prompt injection-only filter:** Narrower scope, misses harmful content detection. Rejected.
