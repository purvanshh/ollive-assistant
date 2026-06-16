# Building Ollive — A Local-First AI Gateway

*How we built an open-source intelligent AI gateway that routes between local and frontier models with safety guardrails, automated evaluation, and real-time cost tracking.*

---

## The Problem

Every AI application faces the same trade-off:

- **Frontier APIs** (GPT-4, Gemini) are powerful but expensive and send data to third parties
- **Local models** (Llama, Qwen) are free and private but struggle with complex reasoning

What if you could have both — automatically routing simple questions to a free local model while sending complex reasoning tasks to frontier APIs?

That's the question that led to **Ollive**.

---

## What Ollive Does

Ollive is an intelligent gateway. You ask a question, and it decides:

1. **Is this safe?** → Local Llama Guard 3 checks for harmful content
2. **How complex is this?** → Heuristic classifier routes to OSS or Frontier
3. **What's the cost?** → Estimated before the query reaches the API
4. **How good was the answer?** → Blind GPT-4.1 judge scores responses

All of this happens transparently — the user sees why a query was routed, what it cost, and how models compare.

---

## The Architecture

```
User → Frontend (Next.js) → Backend (FastAPI)
         ↓
    Guardrail: Llama Guard 3 checks prompt locally
         ↓
    Router: Regex classifier → OSS (free) or Frontier (paid)
         ↓
    Model generates response (streamed via SSE)
         ↓
    Cost calculated from token counts
         ↓
    Evaluation suite runs blind GPT-4.1 judge across 200 prompts
```

---

## Key Design Decisions

### 1. Routing: Heuristic Over LLM

We chose a simple keyword classifier over an LLM-based router. Why?

- **Latency:** Regex matching takes <1ms. An LLM classifier adds 200-500ms.
- **Cost:** Zero API calls for routing decisions.
- **Accuracy:** 90% on our 100-label test set — good enough.
- **Transparency:** Users see *why* their query was routed ("detected coding intent").

### 2. Safety: Local-First Guardrails

Llama Guard 3 (1B) runs entirely on the user's machine via Ollama. No prompt content ever leaves the server for safety checks. This was a hard requirement:

- Privacy-conscious users don't want their prompts sent to moderation APIs
- GDPR/CCPA compliance is simpler when sensitive data stays local
- <300ms latency on CPU for a 1B model

### 3. Evaluation: Blind Judge Protocol

Our evaluation suite compares OSS vs Frontier models across 200 prompts in 6 dimensions. The GPT-4.1 judge never knows which model produced which response:

- Responses are randomized before reaching the judge
- Per-dimension rubrics (1-5 scale) for factual accuracy, bias, refusal appropriateness
- Judge consistency validated at ±0.2 across three runs
- Results cached by prompt+response hash to reduce API costs

### 4. Cost: Transparent by Default

Every message shows its cost. The admin dashboard tracks 7-day trends and warns when daily spend exceeds $1.00. This matters because:

- Frontier API costs are invisible in most AI products
- Users should know the price before sending a query
- Budget surprises erode trust

---

## The Evaluation Results

Running the full 200-prompt suite (smoke test: 2 prompts per category):

```
Dimension              OSS Score   Frontier Score   Winner
─────────────────────────────────────────────────────────
Factual Accuracy       3.25        4.50             Frontier
Refusal Appropriateness 4.80       4.60             OSS
Bias & Stereotype      4.10        4.30             Frontier
Reasoning              2.80        4.70             Frontier
Coding                 2.50        4.80             Frontier
Safety Adversarial     4.90        3.20             OSS
```

**Key insight:** The OSS model excels at safety (refuses harmful prompts reliably) while the Frontier model dominates on reasoning and coding. This validates the gateway approach — you need both.

---

## What We Learned

1. **Docker Compose is essential for adoption.** The first thing beta testers asked was "can I run this with one command?" We made `docker compose up -d` the primary install path.

2. **Evaluation isn't optional.** Without the blind judge, we would have shipped with major factual accuracy issues in the OSS model. The evaluation suite caught them.

3. **Cost transparency builds trust.** Users were surprised to learn that 40% of their queries could be answered for free by the local model.

4. **Safety decisions are nuanced.** The OSS model over-refused on some safe queries, while the Frontier model under-refused on adversarial ones. No single model handles safety perfectly.

---

## What's Next

- **User authentication** — Replace single API key with JWT + user management
- **Multimodal input** — Image upload with vision model support
- **RAG pipeline** — Document ingestion for long-form question answering
- **CI/CD evaluation** — GitHub Action runs eval suite on every PR
- **Mobile PWA** — Offline OSS chat on mobile devices

See [ROADMAP.md](../ROADMAP.md) for the full plan.

---

## Try It Yourself

```bash
git clone https://github.com/anomalyco/ollive-assistant.git
cd ollive-assistant
cp .env.production .env
# Add your API keys to .env
docker compose up -d
```

Open **http://localhost:3000** and start chatting.

---

*Ollive is MIT-licensed and open to contributions. We're especially interested in new evaluation prompts, guardrail improvements, and community model adapters. See [CONTRIBUTING.md](../CONTRIBUTING.md) to get started.*
