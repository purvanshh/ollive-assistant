# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

**Do not open public issues for security vulnerabilities.**

Instead, report them privately to the maintainers:

1. Email: security@ollive.dev
2. Include detailed steps to reproduce
3. Expected response within 48 hours

We follow a coordinated disclosure process:
- Acknowledge receipt within 48 hours
- Validate and assess severity within 5 business days
- Release a fix and advisory within 30 days
- Credit the reporter (unless anonymity requested)

## Security Architecture

Ollive implements defense-in-depth for AI safety:

1. **Local Guardrails:** Llama Guard 3 (1B) runs entirely locally — prompt content never leaves the server for safety checks
2. **API Key Authentication:** All endpoints require `X-API-Key` header
3. **Rate Limiting:** 30 requests/minute per IP via slowapi
4. **Input Validation:** Pydantic models validate all request bodies; file uploads validated by MIME type + magic bytes with 10MB cap
5. **PII Redaction:** Configurable regex-based PII scrubbing on file uploads
6. **Audit Logging:** All guardrail blocks, authentication failures, and admin actions logged to `audit_logs` table
7. **Cost Controls:** Daily budget tracking with configurable warning threshold

## Recommended Deployment Practices

1. Change the default `API_KEY` in `.env` to a strong random string
2. Use HTTPS in production (reverse proxy with Let's Encrypt)
3. Set restrictive CORS origins (not `*`)
4. Run Ollama with `OLLAMA_ORIGINS=localhost` restriction
5. Rotate API keys for cloud providers regularly
6. Monitor the `audit_logs` table for suspicious patterns
7. Keep dependencies updated (`pip-audit`, `npm audit`)
