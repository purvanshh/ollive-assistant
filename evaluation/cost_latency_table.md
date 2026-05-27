# Cost & Latency Analysis

| Model | Avg Latency (ms) | p95 Latency (ms) | Avg Tokens | Cost per 1k calls ($) |
|-------|------------------:|-----------------:|-----------:|----------------------:|
| OSS (Qwen 0.5B) | 4606.76 | 10781.00 | 161.80 | 0.00 |
| Frontier (gpt-4.1) | 2713.52 | 7142.00 | 196.78 | 0.8226 |

### Notes
- OSS latency is measured from actual local inference runtime and is suitable for HF Spaces CPU benchmarking.
- Frontier token counts come from OpenAI usage objects, including tool-call follow-up requests when present.
- Frontier cost per 1k calls uses the configured model's public input/output pricing.
