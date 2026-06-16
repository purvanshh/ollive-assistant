# ADR 004: Cost Tracking & Budget Management

**Status:** Accepted
**Date:** 2026-06-16
**Deciders:** Ollive engineering team

## Context

Ollive routes to both free (OSS) and paid (Frontier API) models. Users need visibility into costs per message, and administrators need budget controls to prevent unexpected API bills.

## Decision

We implement **per-message cost calculation** with **daily budget tracking** and a configurable warning threshold ($1.00/day default).

### Cost Calculation

```python
cost = (input_tokens * INPUT_PRICE + output_tokens * OUTPUT_PRICE) / 1_000_000
```

Pricing is derived from public API rates:

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| GPT-4.1 | $2.00 | $8.00 |
| GPT-4.1-mini | $0.40 | $1.60 |
| Gemini 2.5 Flash | $0.15 | $0.60 |
| OSS (Qwen) | $0.00 | $0.00 |

### Budget Architecture

1. **Per-message:** Cost stored in `messages.cost_usd` column
2. **Per-request:** Cost returned in SSE stream metadata
3. **Pre-flight estimate:** Cost estimator runs client-side before sending prompt
4. **Daily aggregation:** Admin dashboard queries `SUM(cost_usd) WHERE created_at >= today`
5. **Warning:** If daily spend > $1.00, admin dashboard shows red warning banner
6. **Extensibility:** Threshold is configurable; future versions can add hard caps

### UI Surface

- **Chat:** Cost badge on each assistant message + pre-send estimate for frontier-bound queries
- **Admin:** 7-day cost trend chart, daily spend vs budget gauge, model cost breakdown
- **API:** Cost included in SSE stream events

## Consequences

### Positive
- Users know cost before sending expensive queries
- Free OSS model usage is clearly indicated
- Administrators have real-time cost visibility
- All costs are auditable via database

### Negative
- Cost estimates are approximate (token count estimated from character length)
- Actual token counts depend on model tokenizer (not available pre-flight)
- Budget warning is passive (doesn't block requests)
- No per-user cost quotas in MVP

## Alternatives Considered

1. **Post-hoc only (no pre-flight):** Cheaper to implement but users get surprise bills. Rejected.
2. **Hard budget cap:** Blocks requests over limit. Good for production but too restrictive for demo/MVP.
3. **Langfuse cost tracking:** Adds external dependency. Used for observability but not as primary cost store.
4. **Third-party billing (LemonSqueezy/Stripe):** Overkill for MVP with free OSS option. Deferred to post-MVP.
