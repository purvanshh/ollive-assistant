# ADR 001: Model Routing Strategy

**Status:** Accepted
**Date:** 2026-06-16
**Deciders:** Ollive engineering team

## Context

Ollive operates two tiers of AI models: a local open-source model (Qwen2.5-0.5B-Instruct via Ollama) and frontier cloud APIs (Gemini 2.5 Flash, GPT-4.1). We need an intelligent routing system that balances cost, latency, and capability by sending each query to the most appropriate model.

## Decision

We use a **lightweight heuristic classifier** (regex + keyword matching) as the primary routing mechanism with **frontier fallback** when confidence is low.

### Routing Categories

| Intent | Examples | Target Model | Rationale |
|--------|----------|-------------|-----------|
| `simple_chat` | "What is 2+2?", "Hello" | OSS | Low complexity, near-zero cost |
| `calculator` | "Compute 15% of 200" | OSS | Deterministic via tool |
| `reasoning` | "Explain why..." | Frontier | Requires deeper analysis |
| `math` | "Solve integral of..." | Frontier | Complex symbolic reasoning |
| `coding` | "Write a Python function..." | Frontier | Code generation quality |
| `multimodal` | "Analyze this image..." | Frontier | OSS model lacks vision |

### Heuristic Rules

1. Extract keywords from user prompt (case-insensitive)
2. Match against category-specific keyword lists
3. If confidence >= 0.7 for OSS-suitable category → route to OSS
4. Otherwise → route to Frontier
5. User can override routing via UI model selector

## Consequences

### Positive
- ~90% routing accuracy on 100 manually labeled test queries
- OSS handles ~40% of queries with zero API cost
- Transparent to users (routing reason displayed in UI)
- No additional latency (regex matching is <1ms)

### Negative
- Keyword matching fails on edge cases (ambiguous queries)
- Requires periodic keyword list updates
- Can't handle truly conversational context (relies on single-turn analysis)

## Alternatives Considered

1. **LLM-based classifier (GPT-4.1-mini):** Higher accuracy but adds 200-500ms latency and ~$0.0001 per classification. Rejected for latency budget.
2. **Always-frontier:** Simplest but wastes API costs on trivial queries. Rejected.
3. **Always-OSS:** Would fail on complex reasoning tasks. Rejected.
4. **Embedding similarity + kNN:** Complex to maintain and calibrate. Rejected for MVP.
