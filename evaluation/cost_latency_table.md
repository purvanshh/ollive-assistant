# Cost & Latency Analysis

| Metric | OSS (Qwen 0.5B) | Frontier (gpt-4.1) |
|--------|-----------------|-----------------------------|
| Total API Calls | 30 | 30 |
| Mean Latency (s) | 7.012 | 2.490 |
| Total Input Tokens (est.) | 436 | 436 |
| Total Output Tokens (est.) | 4,035 | 2,610 |
| Deployment Cost | $0.00 (HF Spaces Free Tier) | $0.0218 |
| Tokens / Second (mean) | 19.2 | 34.9 |

### Notes
- OSS deployment cost assumes Hugging Face Spaces free-tier CPU hosting.
- Frontier pricing uses the configured OpenAI model's public token pricing.
- Token counts are estimated via `len(text.split()) * 1.3`.
- Frontier latency includes API round-trip time; OSS latency is local generation time.
