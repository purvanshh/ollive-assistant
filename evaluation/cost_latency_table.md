# Cost & Latency Analysis

| Model | Avg Latency (ms) | p95 Latency (ms) | Avg Tokens | Cost per 1k calls ($) |
|-------|------------------:|-----------------:|-----------:|----------------------:|
| OSS (Qwen 0.5B) | 8.17 | 9.00 | 0.00 | 0.00 |
| Frontier (gpt-4.1) | 1284.50 | 1535.00 | 302.25 | 0.9530 |

### Notes
- OSS latency is measured from actual local inference runtime and is suitable for HF Spaces CPU benchmarking.
- Frontier token counts come from OpenAI usage objects, including tool-call follow-up requests when present.
- Frontier cost per 1k calls uses the configured model's public input/output pricing.
