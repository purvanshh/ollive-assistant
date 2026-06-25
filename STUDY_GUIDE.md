# RiskPilot — Mastery Study Guide

> **Developer:** Purvansh  
> **Project:** Loan Approval Multi-Agent Underwriter  
> **Goal:** Achieve mastery-level understanding across all owned phases  
> **Commits:** 36 total, ~2,787 insertions across 100+ files (initial commit)

---

## Table of Contents

1. [Project Overview & Mental Model](#1-project-overview--mental-model)
2. [Deep-Dive by Phase](#2-deep-dive-by-phase)
3. [Interconnection Map](#3-interconnection-map)
4. [Code Deep-Dives (Critical Files)](#4-code-deep-dives-critical-files)
5. [Testing Strategy](#5-testing-strategy)
6. [Common Pitfalls & Debugging Guide](#6-common-pitfalls--debugging-guide)
7. [Enhancement Questions](#7-enhancement-questions)
8. [Interview Prep Section](#8-interview-prep-section)
9. [Self-Assessment Checklist](#9-self-assessment-checklist)
10. [Quick Reference Cards](#10-quick-reference-cards)

---

## 1. Project Overview & Mental Model

### System in 3 Minutes

RiskPilot is a **multi-agent AI system** that automates loan underwriting. A loan application flows through four specialized AI agents arranged as a **directed acyclic graph (DAG)** in LangGraph:

1. **KYC Agent** — Parses uploaded documents (ID, pay slips, bank statements), extracts fields, detects fraud
2. **Credit Agent** — Computes credit score, DTI ratio, risk category, default probability
3. **Policy Agent** — Retrieves lending policies via RAG (ChromaDB + BGE embeddings), validates compliance
4. **Arbitrator Agent** — Aggresses signals from all agents, resolves conflicts via weighted voting, produces a recommendation

**Every recommendation** must be reviewed by a human loan officer before any action reaches the applicant (mandatory HITL). All decisions are logged to an append-only audit trail.

### Contributions at a Glance (36 Commits)

| Area | Commits | Key Hashes |
|------|---------|------------|
| **Core Architecture** — initial 4-agent graph, all source files, initial tests | 1 mega-commit | `011b884` (+2,787 lines, 64 files) |
| **Project Tooling** — Makefile, pre-commit, .flake8, pyproject.toml, .gitignore, .env.example | 2 | `02ccaa6`, `10183d6` |
| **State Schema** — LoanApplicationState, serialization, validation decorators | 1 | `54bc800` |
| **Document Processing** — PDF/image parsing, field extraction (LLM + regex), synthetic PDF generator, audit logger | 1 | `037e3a4` (+2,158 lines, 45 files) |
| **KYC Agent** — verification, fraud detection, retry routing | 1 | `ada51d5` |
| **Input Guardrails** — Pydantic schema, file type/size checks | 1 | `601c756` |
| **Demo & Data Loader** — run_demo_cases.py, data_loader.py, timeout on parsing | 2 | `a07da77`, `a790bc6` |
| **Resilience** — @graceful_fallback, @timeout_resilience, tests | 1 | `2997dc4` |
| **Flask Frontend** — Full web app, 20 test cases, SPA, UI/UX | 8 | `96b8299`, `731bcbc`, `622913f`, `1d38d15` + 4 more |
| **Flask Security** — API key auth, rate limiting, thread-safe state, test_api_security.py | 2 | `26b5bcc`, `1def38b` |
| **UI/UX Refinements** — Fast mode toggle, gpt-4o-mini migration, markdown stripping, log suppression | 6 | `7b0a9de`, `e6e28ea`, `b749068`, `088e8f5`, `27a64dc`, `647b0aa` |
| **Bug Fixes** — RAG retriever post-merge, LangSmith TypeError, Streamlit ModuleNotFound, empty ChromaDB indexing, bypassed agent nodes | 5 | `5c4ee71`, `1a9f7ac`, `d29530d`, `33925df`, `00ec9b7` |
| **Documentation & Config** — README, general guidelines policy, LangSmith config | 4 | `35359ee`, `71fede2`, `2852b1f`, `469ab18` |
| **LangSmith** — env var normalization, project config | 1 | `c5bbe78` |

**Test files authored:** `test_state.py`, `test_kyc.py`, `test_guardrails.py`, `test_resilience.py`, `test_api_security.py`, `test_observability.py`, `test_document_tools.py`

```text
PDF Upload / JSON Input
        │
        ▼
┌───────────────────┐
│  Input Guardrails  │  Pydantic schema, doc count (≥3), file size (≤10MB), file type
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│   KYC Agent       │  Parse PDFs/images, extract fields (LLM or regex), detect fraud
│                    │  Routes: clean → Credit, missing docs → Retry, fraud → Human Review
└────────┬──────────┘
         │ (clean)
         ▼
┌───────────────────┐
│  Credit Agent     │  PRD formula: 300 + (income/1000)*10 + emp_months*2 - dti*200
│                    │  Risk: ≥720 low, ≥650 medium, ≥580 high, <580 very_high
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Policy Agent     │  RAG over 6 policy docs (ChromaDB). Checks: min 650 credit,
│                   │  DTI≤45% (hard 50%), LTV≤80% (hard 85%), emp≥12mo (hard deny <6mo)
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Arbitrator Agent │  Weighted vote: Sum(confidence_i × lean_i) / Sum(confidence_i)
│                    │  Conflict detection, risk flags, → approve/deny/review_required
└────────┬──────────┘
         │ (always)
         ▼
┌───────────────────┐
│  Human-in-Loop    │  Mandatory officer review → approve/deny/override
└────────┬──────────┘
         │
         ▼
    Final Status: approved | denied | under_review
```

### ASCII Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     RiskPilot — System Architecture                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌───────┐ │
│  │  Flask    │    │ Streamlit│    │   CLI    │    │ Jupyter  │    │ Tests │ │
│  │  UI/API  │    │ Dashboard│    │  python  │    │ Notebook │    │ 155   │ │
│  │ :8501    │    │          │    │ -m src   │    │          │    │ tests │ │
│  └────┬─────┘    └──────────┘    └────┬─────┘    └──────────┘    └───────┘ │
│       │                                │                                    │
│       └──────────────┬─────────────────┘                                    │
│                      ▼                                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    LangGraph State Machine                            │   │
│  │  ┌──────┐    ┌──────┐    ┌──────┐    ┌────────┐    ┌─────────┐     │   │
│  │  │ KYC  │───►│Credit│───►│Policy│───►│Arbitra-│───►│ Human   │     │   │
│  │  │ Node │    │ Node │    │ Node │    │ tor    │    │ Review  │     │   │
│  │  └──┬───┘    └──────┘    └──────┘    │ Node   │    │ Node    │     │   │
│  │     │                                └────────┘    └─────────┘     │   │
│  │     ├──► retry (missing docs)                                      │   │
│  │     └──► human_review (fraud)                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    Shared State: LoanApplicationState                │   │
│  │  ┌─────────────┬───────────┬────────────┬──────────────┬──────────┐ │   │
│  │  │applicant_   │ documents │ kyc_output │ credit_output│policy_   │ │   │
│  │  │data (dict)  │[Extracted│ (dict)     │(CreditRisk   │output    │ │   │
│  │  │             │Document] │            │ Output)      │(Policy    │ │   │
│  │  ├─────────────┼───────────┼────────────┼──────────────┤ Output)  │ │   │
│  │  │arbitrator_  │human_    │final_status│ error_log    │ state_   │ │   │
│  │  │output       │decision  │            │ [str]        │ version  │ │   │
│  │  └─────────────┴───────────┴────────────┴──────────────┴──────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────┐  ┌───────────────────┐  ┌─────────────────────┐          │
│  │  ChromaDB   │  │  Sentence-        │  │  Audit Logger       │          │
│  │  (RAG)      │  │  Transformers     │  │  logs/audit.jsonl   │          │
│  │  lending_   │  │  BAAI/bge-small-  │  │  Append-only JSONL  │          │
│  │  policy     │  │  en-v1.5          │  │                     │          │
│  └─────────────┘  └───────────────────┘  └─────────────────────┘          │
│                                                                              │
│  ┌─────────────┐  ┌───────────────────┐  ┌─────────────────────┐          │
│  │  Guardrails │  │  Resilience        │  │  LangSmith          │          │
│  │  Input/     │  │  @graceful_fallback│  │  Traces per run     │          │
│  │  Output     │  │  @timeout(30s)     │  │  trace_id on state  │          │
│  └─────────────┘  └───────────────────┘  └─────────────────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Core Business Problem

Traditional loan underwriting is **slow, inconsistent, and labor-intensive**. A human officer must:

- Manually review identity documents
- Calculate financial ratios by hand
- Search through policy documents for applicable rules
- Make judgment calls on borderline cases
- Document every decision for regulatory compliance

RiskPilot automates the mechanical parts while keeping the human **accountable and in control**.

### Multi-Agent Philosophy

**Why multiple agents instead of one LLM call?**
- **Separation of concerns** — Each agent has a focused responsibility
- **Testability** — Each agent can be tested independently with mocks
- **Debugability** — When something fails, you know exactly which agent failed
- **Auditability** — Each agent's output is logged separately
- **Replaceability** — Swap out a scoring model or a policy doc without touching other agents
- **Explainability** — The arbitrator can cite exactly which agent(s) disagreed

**Why LangGraph?**
- **Explicit state machine** — The graph topology is visible, auditable, and easy to modify
- **Conditional routing** — Fraud goes directly to human review; missing docs trigger retry
- **State management** — Single typed state object passed between nodes, no hidden side effects
- **LangSmith integration** — Automatic traces per node, per run, for free
- **Pydantic validation** — Every node's input and output is schema-validated via `@validate_state`

---

## 2. Deep-Dive by Phase

### Phase 1: Core Architecture

**Commit:** `011b884` — Initial complete architecture (+2,787 lines, 64 files)

**What was built:**
The foundational project structure, package skeleton, all 4 agents (KYC, Credit, Policy, Arbitrator), LangGraph orchestration (state/edges/graph), policy tools, guardrails, RAG pipeline (embeddings, policy loader, vector store), Streamlit dashboard, and initial test suite. This single commit established the entire project's architecture.

**Why it exists:**
Without a shared state schema, agents would produce incompatible outputs. The decorator chain ensures every node's input and output conforms to contract.

**How it works:**

```python
# src/graph/state.py — The heart of the system

class LoanApplicationState(SerializableModel):
    application_id: str          # Unique identifier
    trace_id: Optional[str]      # LangSmith trace linking
    applicant_data: Dict[str, Any]  # Raw inputs from form/JSON
    documents: List[ExtractedDocument] = []
    kyc_output: Optional[Dict[str, Any]] = None
    credit_output: Optional[CreditRiskOutput] = None
    policy_output: Optional[PolicyCheckOutput] = None
    arbitrator_output: Optional[ArbitratorOutput] = None
    human_decision: Optional[HumanDecision] = None
    final_status: Optional[Literal["approved", "denied", "under_review"]] = None
    error_log: List[str] = []
    state_version: str = "1.0.0"
    updated_at: Optional[str] = None
```

The `@validate_state` decorator wraps every agent node:
1. Accepts `dict` or `LoanApplicationState`
2. Validates input conforms to schema
3. Runs the node function
4. Merges returned dict into a copy of original state
5. Validates the merged result conforms to schema
6. Stamps `updated_at` timestamp

**Key files:**
- `src/graph/state.py` — The full state schema + all 3 decorators

**Design decisions:**
- **Dict return from nodes instead of mutating state** — Pure functional style; each node returns updates to merge. This makes testing trivial (call a node, inspect the dict).
- **SerializableModel base** — Wraps Pydantic v2's `model_dump` / `model_validate` for forward compat. The `state_to_dict()` alias exists for PRD audit-trail compliance.
- **`stamp()` method** — Returns a copy with updated_at set; the decorator calls this automatically, so every mutation is timestamped.

**Gotchas:**
- ⚠️ The `@validate_state` decorator runs **before** `@graceful_fallback`. If validation fails, the error propagates **before** fallback can catch it.
- 💡 Pro tip: `@validate_state` is applied outermost, so `@graceful_fallback` catches both real agent errors AND timeout errors (from `@timeout_resilience` which is innermost).

---

### Phase 2: State Schema & Validation

**Commit:** `54bc800` — Finalized LoanApplicationState schema with serialization methods, validation decorators, and test_state.py (+168 lines, 13 files)

**What was built:**
The `LoanApplicationState` Pydantic schema, `SerializableModel` base class with `to_dict()`/`from_dict()`/`validate_state_dict()`, and the `@validate_state` decorator that enforces schema compliance on every agent node's input and output.

**Why it exists:**
State management is the backbone of a multi-agent system. Every agent reads from and writes to the same state object. Without a typed, validated schema, agents would silently produce incompatible outputs, leading to runtime errors that are hard to debug.

**How it works:**
```python
class SerializableModel(BaseModel):
    def to_dict(self) -> Dict[str, Any]:
        if hasattr(self, "model_dump"):
            return self.model_dump()  # Pydantic v2
        return self.dict()            # Pydantic v1 fallback

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        if hasattr(cls, "model_validate"):
            return cls.model_validate(data)  # Pydantic v2
        return cls.parse_obj(data)           # Pydantic v1 fallback

    @classmethod
    def validate_state_dict(cls, data: Dict[str, Any]) -> bool:
        cls.from_dict(data)
        return True
```

The `@validate_state` decorator (at `src/graph/state.py:128`) wraps each agent node:
1. Validates input is a valid `LoanApplicationState` or convertible dict
2. Runs the node function
3. Validates the returned dict merges cleanly into a valid state
4. Stamps `updated_at` via `stamp()`

**Key files:**
- `src/graph/state.py` — `SerializableModel` (line 12), `LoanApplicationState` (line 87), `validate_state` (line 128)
- `tests/test_state.py` — 5 tests covering serialization, decorator success, invalid input, invalid output, wrong type

**Design decisions:**
- **Pydantic v2 with v1 fallback** — `model_dump`/`model_validate` for Pydantic v2, `dict`/`parse_obj` as fallback for anyone stuck on v1
- **`state_to_dict()` alias** — Exists purely for PRD audit-trail compliance (the PRD specified `state_to_dict` as the export method)
- **Dict return contract** — Nodes return dicts (not mutated state objects). This makes testing trivial: call `credit_node(state)`, inspect `result["credit_output"]`.

**Gotchas:**
- ⚠️ The `validate_state_dict` method returns `True` or raises — it never returns `False`. Use it with `try/except` in tests.
- ⚠️ Pydantic v2's `model_validate` is strict about extra fields unless `model_config = {"extra": "allow"}` is set.

---

### Phase 4: Document Processing

**Commit:** `037e3a4` — Document parser, PDF extractor, synthetic PDF generator, 20+ synthetic documents, audit logger (+2,158 lines, 45 files)

**What was built:**
The document parsing pipeline: `parse_pdf()` via PyPDF2, `parse_image()` via Pillow/pytesseract, `parse_document()` as the unified entry point with file-type/size validation, `detect_document_type()` via filename + content heuristics, and `extract_fields()` with LLM (GPT-4o-mini) and regex fallback.

**Why it exists:**
Loan applications arrive as PDFs, images, or text. The system must extract structured data (name, income, employer, tenure) from unstructured documents reliably, with graceful degradation.

**How it works:**

```
File path → parse_document()
  ├── Check file size ≤ 10MB
  ├── Check extension ∈ {pdf, jpg, png, txt, md}
  ├── .pdf → PyPDF2.PdfReader → text
  ├── .jpg/.png → Pillow → pytesseract OCR (or simulated)
  └── .txt/.md → raw file read
       │
       ▼
extract_fields(text, doc_type)
  ├── OPENAI_API_KEY set? → GPT-4o-mini via langchain_openai
  │     Prompt: extract JSON fields per doc_type
  │     Parse JSON response, normalize confidence
  └── No API key → extract_fields_fallback()
        Regex patterns for name, DOB, income, debt, employer, tenure
```

```python
# Key flow in kyc_node (parallel document processing):
with concurrent.futures.ThreadPoolExecutor() as executor:
    results = list(executor.map(_process_single_doc, state.documents))
```

**Key files:**
- `src/tools/document_tools.py:17-91` — parse_pdf, parse_image, parse_document
- `src/tools/document_tools.py:135-284` — extract_fields_fallback, extract_fields

**Design decisions:**
- **LLM-first, regex-fallback** — GPT-4o-mini is remarkably reliable at structured extraction. When unavailable (no API key, network error), the regex fallback is surprisingly robust for synthetic documents because it has hardcoded synthetic data patterns (e.g., "employed at TechCorp for 3 years").
- **ThreadPoolExecutor** — Documents are independent, so parsing in parallel is safe. The executor is created fresh per node invocation.
- **`@timeout_resilience(30.0)` on parse_document and extract_fields** — PDF parsing can hang on corrupted files.

**Gotchas:**
- ⚠️ The regex fallback's hardcoded name/employer mappings (lines 196-210) are specific to the synthetic documents. In production, you'd need a more robust extractor.
- ⚠️ `parse_image()` falls back to `"Simulated OCR text for image: {filename}"` if pytesseract isn't installed — this is fine for the demo but produces no real text.
- 💡 Pro tip: The `parse_document` is also decorated with `@timeout_resilience`, making it resilient to hanging PDFs even when called outside the graph.

---

### Phase 5: KYC Agent

**Commit:** `ada51d5` — KYC agent with verification logic, mismatch flag detection, retry routing, and test_kyc.py (+158 lines, 28 files)

**What was built:**
The `kyc_node()` function — the first node in the LangGraph pipeline. It: validates documents are present, processes each document (parsing + field extraction), checks for 3 required types (`id_proof`, `bank_statement`, `pay_slip`), detects fraud via income mismatch (>20%) and name mismatch across documents, and produces a KYC output dict with confidence, fraud flags, and verified fields.

**Why it exists:**
Know Your Customer (KYC) is the regulatory gate. No loan can proceed without verified identity and income. This agent establishes trust in the data before financial calculations begin.

**How it works:**

```python
# Simplified kyc_node flow:
def kyc_node(state):
    # 1. Guard: reject empty documents
    if not state.documents:
        raise ValueError("No documents provided")

    # 2. Process documents in parallel
    with ThreadPoolExecutor() as executor:
        results = executor.map(_process_single_doc, state.documents)

    # 3. Check required doc types
    required_types = {"id_proof", "bank_statement", "pay_slip"}
    missing_critical_docs = list(required_types - doc_types)

    # 4. Fraud detection: income mismatch (>20%)
    if pay_slip_income and bank_statement_income:
        diff_ratio = abs(pay_slip_income - bank_statement_income) / max(...)
        if diff_ratio > 0.20:
            fraud_flag = True
            kyc_confidence = min(kyc_confidence, 0.5)

    # 5. Fraud detection: name mismatch
    if id_name and pay_slip_name:
        if id_name.strip().lower() != pay_slip_name.strip().lower():
            fraud_flag = True
            kyc_confidence = min(kyc_confidence, 0.4)
```

**Key files:**
- `src/agents/kyc_agent.py` — The full KYC node (188 lines)
- `src/tools/document_tools.py` — parse_document, extract_fields (called by KYC)
- `src/graph/edges.py:9-32` — `route_after_kyc()` — conditional routing logic

**Design decisions:**
- **Income comparison across documents** — If pay slip says $5,000/mo and bank statement says $4,000/mo, the 20% discrepancy triggers fraud. This catches application fabrications.
- **Name normalization** — `.strip().lower()` comparison prevents trivial casing mismatches from triggering false fraud flags.
- **Confidence penalties** — Fraud drops confidence to 0.5 (income mismatch) or 0.4 (name mismatch). The arbitrator uses these confidence values in weighted voting.
- **KYC output structure** — Returns a dict (not a Pydantic model) because KYC output has varying fields. The dict is validated indirectly by `@validate_state` when merged back into state.

**Gotchas:**
- ⚠️ If `state.documents` is populated with `ExtractedDocument` objects that contain file **paths** as `extracted_text`, the KYC node will parse them. If they contain raw text, it uses them directly. This dual-mode (path vs. text) is controlled by `data_loader.py`'s `use_pdf_paths` flag.
- ⚠️ The fraud check only runs when both pay_slip AND bank_statement incomes are present. If one is missing, fraud is never flagged for income mismatch — a potential blind spot.

---

### Phase 10: Guardrails

**Commit:** `601c756` — Pydantic input validation schema, file type/size limits, document count checks, audit logging, and test_guardrails.py (+206 lines, 2 files)

**What was built:**
Three guardrail components:
- **Input validation** (`input_validation.py`) — Pydantic schema for applicant data, min 3 documents, file type/size validation, audit logging on violations
- **Output validation** (`output_validation.py`) — Confidence threshold (<0.6 → human review), DTI hard stop (>0.6 → auto-flag), agent conflict detection, mandatory HITL flag
- **Audit logger** (`audit_logger.py`) — Append-only JSONL file at `logs/audit.jsonl` with `AuditLogger` class and module-level convenience functions

**Why it exists:**
Guardrails are the safety net. Input guardrails prevent garbage data from entering the pipeline. Output guardrails catch impossible recommendations (e.g., DTI > 60% should never be auto-approved). The audit logger satisfies PRD §8.3: "All agent outputs, retrievals, and decisions logged."

**How it works:**

```python
# Input validation — called BEFORE graph.invoke()
def validate_application_input(application_data, documents, application_id=None):
    # 1. Pydantic schema: income > 0, monthly_debt >= 0, etc.
    ApplicantDataInputSchema.model_validate(application_data)
    # 2. Document count >= 3
    # 3. File types in {pdf, jpg, png}
    # 4. File size <= 10MB per document
    # 5. Audit log all violations

# Output validation — called AFTER agent nodes
def validate_credit_output(credit_output, application_id=None):
    if credit_output.confidence_score < 0.6:
        flags.append("Confidence below threshold — human review required")
    if credit_output.dti_ratio > 0.6:
        flags.append("DTI exceeds hard stop — auto-flagged")

def validate_system_recommendation(arbitrator_output, credit_output=None):
    # Also checks agent_agreement == "conflict"
    # Always appends mandatory HITL flag
```

**Key files:**
- `src/guardrails/input_validation.py` — Full file (122 lines)
- `src/guardrails/output_validation.py` — Full file (145 lines)
- `src/guardrails/audit_logger.py` — Full file (141 lines)

**Design decisions:**
- **AuditLogger class + module-level functions** — Both are available. The class is useful when you need multiple operations for the same application; the functions are convenient for one-off logging.
- **env-var configurable log path** — `RISKPILOT_AUDIT_LOG` env var overrides the default `logs/audit.jsonl`. Useful for per-deployment log routing.
- **DTI hard stop at 0.6** — Even if the arbitrator says "approve", a DTI > 0.6 forces the recommendation to `review_required`. This is a safety override.
- **Mandatory HITL flag** — Every single recommendation includes the HITL flag, ensuring no output can slip through without human review.

**Gotchas:**
- ⚠️ The input guardrails are NOT called automatically before graph.invoke(). They exist as standalone functions. In the Flask UI, they're called before the pipeline. If someone calls `graph.invoke()` directly, they bypass input guardrails.
- ⚠️ `validate_system_recommendation()` returns `(requires_review_override, flags)`. The `flags` list always includes the HITL message, but `requires_review_override` only returns `True` for actual guardrail violations (not the HITL flag). This means you must ALWAYS check the flags, not just the boolean.

---

### Phase 14: Demo & Data Loader

**Commits:** `a07da77` (scratch/run_demo_cases.py, +129 lines), `a790bc6` (src/tools/data_loader.py, +195 lines)

**What was built:**
- `data_loader.py` — Loads test applications from JSON, resolves PDF paths, constructs `LoanApplicationState`
- `synthetic_docs/` — 20+ synthetic PDFs generated by `scratch/generate_synthetic_pdfs.py` using reportlab
- `test_applications.json` — 20 structured test cases (APP-001 through APP-020)
- `scratch/run_demo_cases.py` — End-to-end demo runner
- `scratch/generate_synthetic_pdfs.py` — PDF generator for test apps

**Why it exists:**
Without test data, you can't demo, test, or develop. The data loader bridges the gap between static JSON test cases and the LangGraph pipeline.

**How it works:**

```python
def build_state_from_app(app, use_pdf_paths=True):
    # For each document in the test case:
    for doc in app["documents"]:
        if use_pdf_paths:
            pdf_path = resolve_pdf_path(app_id, doc_type)
            if pdf_path:
                text_or_path = pdf_path  # KYC will parse the PDF
            else:
                text_or_path = raw_text  # Fallback to embedded text
        else:
            text_or_path = raw_text  # "Fast mode" — no PDF parsing

    return LoanApplicationState(application_id, applicant_data, documents)

def resolve_pdf_path(app_id, doc_type):
    # APP-001 + bank_statement → data/synthetic_docs/APP-001-bank_statement.pdf
    return f"{_SYNTHETIC_DOCS_DIR}/{app_id}-{suffix}.pdf"
```

**Key files:**
- `src/tools/data_loader.py` — The loader (168 lines)
- `scratch/run_demo_cases.py` — Demo runner
- `data/test_applications.json` — 20 test case definitions

**Design decisions:**
- **`use_pdf_paths` flag** — Controls whether the pipeline exercises PDF parsing or uses embedded text. This is critical for test speed: unit tests use `fast_mode=True` (no PDF I/O), while the demo exercises the full pipeline.
- **`iter_states()` generator** — Yields `LoanApplicationState` for every test case. Used by `--all` mode in main.py and the demo runner.
- **20 test cases** — Cover approve, deny, review_required, borderline, fraud, missing docs, low confidence, income mismatch, high DTI, and more.

**Gotchas:**
- ⚠️ PDF paths are OS-dependent. `resolve_pdf_path()` constructs absolute paths using `_PROJECT_ROOT`. If the project is moved, paths break.
- ⚠️ The synthetic PDFs are generated ONCE by `generate_synthetic_pdfs.py`. If you add a new test case, you must regenerate PDFs or use `fast_mode=True`.
- 💡 Pro tip: Always set `use_pdf_paths=False` in unit tests to avoid I/O. Only `test_document_tools.py` and the demo runner should exercise real PDF parsing.

---

### Phase 16: Resilience

**Commit:** `2997dc4` — @graceful_fallback and @timeout_resilience decorators on all 4 agents, test_resilience.py (+265 lines, 6 files)

**What was built:**
The three-layer decorator system protecting every agent node:
1. `@timeout_resilience(seconds)` — Wraps node in `ThreadPoolExecutor` with timeout
2. `@graceful_fallback(type)` — Catches exceptions, returns conservative fallback per agent type
3. `@validate_state` — Validates schema in/out (already covered in Phase 1)

**Why it exists:**
In production, things fail: LLM calls hang, PDFs are corrupted, network partitions occur. Resilience ensures the system degrades gracefully instead of crashing.

**How it works:**

```python
# Decorator chain on every agent node:
@validate_state          # 1. Validate (outermost)
@graceful_fallback("kyc") # 2. Fallback (middle)
@timeout_resilience(30.0) # 3. Timeout (innermost)
def kyc_node(state):
    ...

# Execution order (innermost to outermost):
timeout_resilience wraps the function → graceful_fallback wraps that → validate_state wraps that

# On invocation:
validate_state validates input → graceful_fallback sets up try/except → timeout_resilience submits to executor → ... real code runs ...
# On exception:
graceful_fallback catches it → returns fallback dict for the agent type
```

```python
# Fallback types — what gets returned:
# KYC fallback:
{
    "kyc_output": {
        "status": "failed",
        "missing_critical_docs": True,
        "missing_docs_list": ["id_proof", "bank_statement", "pay_slip"],
        "fraud_flag": False,
        "confidence": 0.0,
        "verified_fields": { ... }
    }
}

# Credit fallback:
CreditRiskOutput(score=300, risk="very_high", dti=1.0, confidence=0.0)

# Policy fallback:
PolicyCheckOutput(passed=False, violations=["System error: ..."])

# Arbitrator fallback:
ArbitratorOutput(recommendation="review_required", confidence=0.0, agreement="conflict")
```

**Key files:**
- `src/graph/state.py:175-282` — timeout_resilience and graceful_fallback decorators
- `tests/test_resilience.py` — 18 tests verifying all 4 fallback types + timeout

**Design decisions:**
- **Conservative defaults** — All fallbacks push toward denial/review. A failed agent defaults to the safest outcome (e.g., credit score 300, DTI 1.0, policy failed, review required).
- **Error logging** — All errors are appended to `state.error_log`. This means downstream agents can inspect what went wrong.
- **Validation error propagation** — Certain errors (`"Validation Error"` and `"No documents"`) are RE-RAISED by `graceful_fallback`, not caught. This prevents the system from silently swallowing critical input validation failures.
- **ThreadPoolExecutor for timeout** — A single-thread executor per invocation. The `future.result(timeout=seconds)` call raises `TimeoutError` if the function doesn't complete in time.

**Gotchas:**
- ⚠️ `@timeout_resilience` creates a new `ThreadPoolExecutor` on EVERY invocation. For high-throughput systems, a shared executor with cleanup would be better.
- ⚠️ The timeout decorator does NOT cancel the underlying thread (Python threads can't be safely killed). The thread continues running but its result is ignored. This could cause resource leaks under heavy load.
- ⚠️ The decorator order matters: `@graceful_fallback` must be INSIDE `@validate_state` so that fallback catches validation errors from the node's own outputs, but OUTSIDE `@timeout_resilience` so that fallback catches timeout errors.

---

### Flask Frontend & Security

**Commits:** `96b8299` (initial Flask app + 700-line index.html, +2,087 lines), `731bcbc` (20 test cases, citations, state persistence), `622913f` (status badges, pipeline viz), `1d38d15` (reset switch), `26b5bcc` (API key auth + rate limiting + thread safety, 242 lines), `1def38b` (QA audit + test_api_security.py, 485 lines)

**UI/UX refinements (6 commits):** `7b0a9de` (bug fix, scrollbar, color palette), `e6e28ea` (hide rationale until pipeline runs), `b749068` (hide decision panel on final status), `088e8f5` (reordered rationale component), `27a64dc` (strip markdown from RAG chunks), `647b0aa` (fast mode toggle, gpt-4o-mini migration, log suppression)

**What was built:**
- `src/ui/app.py` — Flask web server with three API endpoints + single-page HTML frontend
- `src/ui/templates/index.html` — 1376-line SPA with Tailwind CSS + JavaScript
- `src/ui/app_config.py` — Configuration from environment variables
- Security: API key auth, CORS, rate limiting, request validation, state desync protection
- Plus: fast mode toggle, markdown stripping from RAG chunks, personality mapping for applications, pipeline visualization cards with status badges, reset switch

**Why it exists:**
The CLI is great for development, but loan officers need a GUI. The Flask app serves an interactive dashboard where they can view applications, run the pipeline, inspect agent outputs, and submit decisions.

**How it works:**

```python
# Three API routes:
GET  /api/applications           → List all test applications
POST /api/underwrite/<app_id>    → Run pipeline, return state
POST /api/decision/<app_id>      → Submit officer decision

# Security decorator:
@require_api_key
def decorated(*args, **kwargs):
    # Skip auth in TESTING mode
    # Skip auth if API_KEYS is empty (dev mode)
    # Otherwise check X-API-Key header

# Rate limiting:
limiter = Limiter(key_func=get_remote_address,
                  default_limits=["200 per day", "50 per hour"])
# Decision endpoint: 10 per minute (extra strict)
@limiter.limit("10 per minute")

# State desync protection:
_app_locks = defaultdict(threading.Lock)  # Per-app lock
_PIPELINE_STATE = {}  # In-memory store

# Decision endpoint locks and checks:
with _app_locks[app_id]:
    if app_id not in _PIPELINE_STATE:
        return 400 "Pipeline must be run first"
    if stored["final_status"] in ("approved", "denied"):
        return 409 "Decision already submitted"
    # Apply decision to stored state (preserving agent outputs)
    previous_state = LoanApplicationState.from_dict(stored)
    previous_state.human_decision = HumanDecision(...)
    state_updates = human_review_node(previous_state)
    # Merge and store
```

**Key files:**
- `src/ui/app.py` — Full Flask server (287 lines)
- `src/ui/app_config.py` — Config (43 lines)
- `src/ui/templates/index.html` — SPA frontend (1376 lines)

**Design decisions:**
- **In-memory state store** — `_PIPELINE_STATE` dict holds the pipeline output per app. Simple but lost on server restart. In production, Redis would be used.
- **Per-app locks** — `defaultdict(threading.Lock)` prevents concurrent requests for the same app from corrupting state, without serializing all requests globally.
- **Fast mode toggle** — The frontend sends `fast_mode: true` to skip PDF parsing, useful for development. The default uses full PDF parsing.
- **Second-decision prevention** — Returns HTTP 409 Conflict if a decision was already submitted. This prevents a race condition where two officers submit conflicting decisions.
- **State desync fix** — The decision endpoint uses the STORED pipeline state (not the re-parsed test data). This was Bug-2: previously, the decision endpoint reloaded from `test_applications.json`, losing agent outputs.

**Gotchas:**
- ⚠️ The `_PIPELINE_STATE` is in-memory only. Restarting the Flask server loses all pipeline results.
- ⚠️ The `require_api_key` decorator is OPTIONAL — when `API_KEYS` env var is empty, auth is skipped entirely. Ensure production deployments set `API_KEYS`.
- ⚠️ Rate limiting is in-memory. For multi-process deployments (e.g., gunicorn with multiple workers), use the `RATELIMIT_STORAGE_URI` env var to point to Redis.

---

## 3. Interconnection Map

### Data Flow (PDF Upload → Decision)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       COMPLETE DATA FLOW JOURNEY                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ 1. UPLOAD PHASE                                                             │
│    User uploads: APP-001-id.pdf, APP-001-bank_statement.pdf,                │
│                  APP-001-pay_slip.pdf                                        │
│        │                                                                     │
│        ▼                                                                     │
│                                                                              │
│ 2. INPUT VALIDATION (Guardrails)                                            │
│    ┌──────────────────────────────────────────────┐                        │
│    │ validate_application_input()                  │                        │
│    │ ├── Pydantic: income > 0, debt >= 0, etc.    │                        │
│    │ ├── Doc count >= 3                           │                        │
│    │ ├── File types: pdf/jpg/png                  │                        │
│    │ ├── File size: each ≤ 10MB                   │                        │
│    │ └── Audit log violations                     │                        │
│    └──────────────────────────────────────────────┘                        │
│        │                                                                     │
│        ▼                                                                     │
│                                                                              │
│ 3. KYC AGENT                                                                │
│    ┌──────────────────────────────────────────────┐                        │
│    │ kyc_node(state)                               │                        │
│    │ ├── Guard: documents not empty               │                        │
│    │ ├── ThreadPoolExecutor:                       │                        │
│    │ │   ├── parse_document(pdf_path) → text       │                        │
│    │ │   │     ├── PyPDF2 extract text             │                        │
│    │ │   │     └── @timeout_resilience(30s)        │                        │
│    │ │   └── extract_fields(text, doc_type) → fields│                       │
│    │ │         ├── GPT-4o-mini (if API key)        │                        │
│    │ │         └── Regex fallback                  │                        │
│    │ ├── Check required types: id+pay+bank         │                        │
│    │ ├── Fraud: income mismatch > 20%?             │                        │
│    │ ├── Fraud: name mismatch across docs?         │                        │
│    │ └── Return: extracted_docs + kyc_output       │                        │
│    └──────────────────────────────────────────────┘                        │
│        │                                                                     │
│        ├── missing_critical_docs? ─────► Retry Node                         │
│        │                                    └──► END (under_review)         │
│        ├── fraud_flag? ───────────────────► Human Review Node               │
│        │                                    └──► END                        │
│        └── clean ──────────────────────────► Credit Agent                    │
│                                                                              │
│ 4. CREDIT AGENT                                                             │
│    ┌──────────────────────────────────────────────┐                        │
│    │ credit_node(state)                            │                        │
│    │ ├── Resolve income (KYC override if avail)   │                        │
│    │ ├── dti = monthly_debt / (income/12)         │                        │
│    │ ├── score = 300 + (income/1000)*10 +         │                        │
│    │ │          emp_months*2 - dti*200            │                        │
│    │ ├── risk: ≥720 low, ≥650 med, ≥580 high,     │                        │
│    │ │         <580 very_high                     │                        │
│    │ ├── default_prob = 1 - ((score-300)/550)     │                        │
│    │ ├── confidence: income>0=+0.35, debt>=0=+0.25│                        │
│    │ │              emp≥12=+0.25, ≥6=+0.15,       │                        │
│    │ │              income>20k=+0.15              │                        │
│    │ └── Return: CreditRiskOutput                  │                        │
│    └──────────────────────────────────────────────┘                        │
│        │                                                                     │
│        ▼                                                                     │
│                                                                              │
│ 5. POLICY AGENT (RAG)                                                       │
│    ┌──────────────────────────────────────────────┐                        │
│    │ policy_node(state)                            │                        │
│    │ ├── ltv = loan_amount / property_value       │                        │
│    │ ├── Query ChromaDB with 4 questions:         │                        │
│    │ │   - "Minimum credit score?"                │                        │
│    │ │   - "Maximum DTI ratio?"                   │                        │
│    │ │   - "Employment stability?"                │                        │
│    │ │   - "Maximum LTV for amount?"              │                        │
│    │ ├── policy_validator():                      │                        │
│    │ │   - credit >= 650?                         │                        │
│    │ │   - DTI <= 45%? (hard: 50%)               │                        │
│    │ │   - LTV <= 80%? (hard: 85%)               │                        │
│    │ │   - emp >= 12mo? (hard deny <6mo)         │                        │
│    │ │   - income docs >= 2?                      │                        │
│    │ └── Return: PolicyCheckOutput with chunks    │                        │
│    └──────────────────────────────────────────────┘                        │
│        │                                                                     │
│        ▼                                                                     │
│                                                                              │
│ 6. ARBITRATOR AGENT                                                         │
│    ┌──────────────────────────────────────────────┐                        │
│    │ arbitrator_node(state)                        │                        │
│    │ ├── Map each agent to [-1, +1] lean:        │                        │
│    │ │   KYC: fraud/missing = -1, else +1        │                        │
│    │ │   Credit: low=+1, med=+0.25, high=-0.75,  │                        │
│    │ │           very_high=-1                     │                        │
│    │ │   Policy: passed=+1, failed=-1             │                        │
│    │ ├── weighted_vote = Σ(c_i * lean_i) / Σ(c_i)│                        │
│    │ ├── Conflict rules:                          │                        │
│    │ │   - Fraud → review_required               │                        │
│    │ │   - High/Very_High credit → deny          │                        │
│    │ │   - Policy fail + credit≥700 → conflict   │                        │
│    │ │   - Borderline 650-699 → review           │                        │
│    │ │   - Weighted vote tie-breaker             │                        │
│    │ └── Return: ArbitratorOutput                 │                        │
│    └──────────────────────────────────────────────┘                        │
│        │                                                                     │
│        ▼ (always)                                                            │
│                                                                              │
│ 7. HUMAN REVIEW                                                             │
│    ┌──────────────────────────────────────────────┐                        │
│    │ human_review_node(state)                      │                        │
│    │ ├── If human_decision exists:                │                        │
│    │ │   approve/override_approve → "approved"    │                        │
│    │ │   deny/override_deny → "denied"            │                        │
│    │ └── Else → "under_review"                    │                        │
│    └──────────────────────────────────────────────┘                        │
│        │                                                                     │
│        ▼                                                                     │
│                                                                              │
│ 8. PRE-FLIGHT CHECKS                                                        │
│    ┌──────────────────────────────────────────────┐                        │
│    │ validate_system_recommendation()              │                        │
│    │ ├── Confidence < 0.6? → review               │                        │
│    │ ├── Agent conflict? → review                 │                        │
│    │ ├── DTI > 0.6? → review override            │                        │
│    │ └── Mandatory HITL flag ALWAYS appended     │                        │
│    └──────────────────────────────────────────────┘                        │
│        │                                                                     │
│        ▼                                                                     │
│    final_status = "approved" | "denied" | "under_review"                    │
│    Audit log entry written to logs/audit.jsonl                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Communication

| Component | Talks To | How | Data Passed |
|-----------|----------|-----|-------------|
| KYC Agent | Graph State | Returns dict | `kyc_output`, `documents`, `error_log` |
| Credit Agent | Graph State | Returns dict | `credit_output`, `error_log` |
| Credit Agent | KYC (from state) | Reads `kyc_output.verified_fields` | KYC-verified income override |
| Policy Agent | Graph State + ChromaDB | Reads state, queries vector store | `policy_output`, `error_log` |
| Policy Agent | Credit (from state) | Reads `credit_output` | Credit score, DTI for LTV check |
| Arbitrator | All agents (from state) | Reads `kyc_output`, `credit_output`, `policy_output` | Weighted vote computation |
| Human Review | Graph State | Reads/writes `human_decision` | `final_status` |
| Audit Logger | Any component | Called as function | Writes to `logs/audit.jsonl` |
| Flask API | Graph | `graph.invoke()` | Full `LoanApplicationState` dict |
| Flask API | _PIPELINE_STATE | In-memory dict | Serialized state per app_id |

### State Management Journey

```
Start: LoanApplicationState(application_id, applicant_data, documents)

After KYC:   + kyc_output (dict), documents updated (parsed), error_log extended
After Credit: + credit_output (CreditRiskOutput), error_log extended
After Policy: + policy_output (PolicyCheckOutput), error_log extended
After Arbitrator: + arbitrator_output (ArbitratorOutput), error_log extended
After Human Review: + human_decision (HumanDecision), final_status set
End:          All fields populated, final_status ∈ {approved, denied, under_review}
```

### Resilience Boundaries

```
┌─────────────────────────────────────────────────────────────────────┐
│                      RESILIENCE BOUNDARIES                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Layer 1: @validate_state                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │  Catches: Schema violations (Pydantic ValidationError)          ││
│  │  Action: Re-raises as ValueError (NOT caught by fallback)       ││
│  │  Exception: "Validation Error" and "No documents" errors        ││
│  │  are propagated (by design — these mean STOP).                  ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  Layer 2: @graceful_fallback                                         │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │  Catches: Runtime errors, API failures, logic errors            ││
│  │  Action: Logs error to state.error_log, returns safe fallback   ││
│  │  KYC: status=failed, docs missing, confidence=0.0               ││
│  │  Credit: score=300, risk=very_high, dti=1.0, confidence=0.0    ││
│  │  Policy: passed=False, violations=["System error"]              ││
│  │  Arbitrator: recommendation=review_required                     ││
│  │  Note: Does NOT catch "Validation Error" or "No documents"     ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  Layer 3: @timeout_resilience(30.0)                                  │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │  Catches: Functions that hang > 30 seconds                      ││
│  │  Action: Raises TimeoutError (caught by graceful_fallback)      ││
│  │  Scope: Applied to parse_document, extract_fields, and all      ││
│  │         4 agent nodes                                            ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  Layer 4: MockEmbeddings (embeddings.py)                             │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │  If sentence-transformers fails to load: returns MockEmbeddings ││
│  │  MockEmbeddings returns zero-vectors (768-d)                    ││
│  │  ChromaDB fallback: MockCollection (token-match query)          ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  Layer 5: Agent-level fallback (credit_agent.py)                    │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │  Each agent has its OWN try/except as well (redundant with     ││
│  │  @graceful_fallback but provides agent-specific messages)       ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Code Deep-Dives (Critical Files)

### Top 20 Most Important Files

| # | File | Lines | Why It Matters |
|---|------|-------|----------------|
| 1 | `src/graph/state.py` | 282 | Heart of the system: state schema + 3 decorators |
| 2 | `src/graph/graph.py` | 162 | LangGraph orchestration: nodes, edges, compilation |
| 3 | `src/graph/edges.py` | 41 | Conditional routing logic (KYC → credit/retry/review) |
| 4 | `src/agents/kyc_agent.py` | 188 | Document processing + fraud detection |
| 5 | `src/agents/credit_agent.py` | 130 | Credit scoring + risk classification |
| 6 | `src/agents/policy_agent.py` | 108 | RAG-based policy compliance |
| 7 | `src/agents/arbitrator_agent.py` | 224 | Weighted voting + conflict resolution |
| 8 | `src/tools/credit_tools.py` | 114 | PRD scoring formula + helper functions |
| 9 | `src/tools/policy_tools.py` | 168 | LTV calc, RAG retriever, policy validator |
| 10 | `src/tools/document_tools.py` | 295 | PDF parsing, OCR, field extraction |
| 11 | `src/tools/data_loader.py` | 168 | Test data → state conversion |
| 12 | `src/tools/human_review_tool.py` | 111 | HITL decision collection |
| 13 | `src/rag/embeddings.py` | 59 | BGE embeddings + MockEmbeddings fallback |
| 14 | `src/rag/policy_loader.py` | 115 | Markdown chunking + ChromaDB indexing |
| 15 | `src/rag/vector_store.py` | 77 | ChromaDB wrapper + MockCollection |
| 16 | `src/guardrails/input_validation.py` | 122 | Pydantic schema + doc validation |
| 17 | `src/guardrails/output_validation.py` | 145 | Confidence + DTI hard stop checks |
| 18 | `src/guardrails/audit_logger.py` | 141 | Append-only JSONL audit trail |
| 19 | `src/ui/app.py` | 287 | Flask API + state management |
| 20 | `src/ui/templates/index.html` | 1376 | Full SPA frontend |

### File-by-File Deep Dive

#### 1. `src/graph/state.py` — The Heart

**Purpose:** Defines `LoanApplicationState`, all sub-models, and the 3 decorators that wrap every agent node.

**Key classes/functions:**
- `SerializableModel` (line 12) — Base class with `to_dict()`, `from_dict()`, `validate_state_dict()`
- `LoanApplicationState` (line 87) — The single shared state with 14 fields
- `validate_state` (line 128) — Decorator: validates input, runs node, validates output
- `timeout_resilience` (line 175) — Decorator: ThreadPoolExecutor timeout
- `graceful_fallback` (line 198) — Decorator: catch exceptions, return conservative fallback

**Code snippet worth memorizing:**

```python
# The decorator chain pattern (lines 17-19 in kyc_agent.py):
@validate_state
@graceful_fallback("kyc")
@timeout_resilience(30.0)
def kyc_node(state: LoanApplicationState) -> Dict[str, Any]:
```

This pattern appears on ALL 4 agent nodes. Understand the execution order (inside-out) and what happens when each layer triggers.

#### 2. `src/graph/graph.py` — The Orchestrator

**Purpose:** Builds the LangGraph state machine.

**Key functions:**
- `retry_node()` (line 52) — Handles missing-docs routing; checks for officer override
- `human_review_node()` (line 91) — Applies officer decision or sets under_review
- `_populate_missing_agent_outputs()` (line 16) — Runs skipped agents if they were bypassed (critical for retry path)
- `graph = builder.compile()` (line 162) — The compiled graph object used everywhere

**The graph topology:**

```
kyc → (credit | retry | human_review)
credit → policy
policy → arbitrator
arbitrator → human_review
retry → END
human_review → END
```

#### 9. `src/tools/credit_tools.py` — The Scoring Engine

**Purpose:** All financial calculation functions used by the credit agent.

**Key functions:**
- `calculate_credit_score()` (line 4) — PRD formula: `300 + (income/1000)*10 + emp_months*2 - dti*200`
- `dti_calculator()` (line 35) — `monthly_debt / (annual_income/12)`
- `risk_classifier()` (line 45) — Maps 300-850 to low/medium/high/very_high
- `calculate_default_probability()` (line 63) — Linear: `1 - ((score-300)/550)`
- `calculate_confidence_score()` (line 76) — Data quality scoring (4 factors)

**Code snippet worth memorizing:**

```python
# The PRD credit score formula (line 26):
base_score = 300 + (income / 1000.0) * 10.0 + employment_months * 2.0 - dti * 200.0

# The risk thresholds (line 53-59):
if credit_score >= 720: return "low"
elif credit_score >= 650: return "medium"
elif credit_score >= 580: return "high"
else: return "very_high"

# Default probability (line 72):
prob = 1.0 - ((credit_score - 300) / 550.0)
```

#### 7. `src/agents/arbitrator_agent.py` — The Decision Engine

**Purpose:** Aggregates signals from all agents, computes weighted vote, detects conflicts.

**Key function — the weighted vote:**

```python
def compute_weighted_vote(kyc_confidence, kyc_score,
                          credit_confidence, credit_score_lean,
                          policy_confidence, policy_score_lean):
    weighted_sum = (kyc_confidence * kyc_score +
                    credit_confidence * credit_score_lean +
                    policy_confidence * policy_score_lean)
    total_confidence = kyc_confidence + credit_confidence + policy_confidence
    weighted_score = weighted_sum / total_confidence if total_confidence > 0 else 0.0

    if weighted_score >= 0.25: return "approve"
    elif weighted_score <= -0.25: return "deny"
    else: return "review_required"
```

**The leaning scores (lines 113-122):**

```python
# KYC lean
kyc_lean = -1.0 if (kyc_fraud or kyc_missing_docs) else 1.0

# Credit lean
if   credit_risk == "low":       credit_lean = 1.0
elif credit_risk == "medium":    credit_lean = 0.25
elif credit_risk == "high":      credit_lean = -0.75
else:                            credit_lean = -1.0  # very_high

# Policy lean
policy_lean = 1.0 if policy_passed else -1.0
```

**Conflict detection rules (lines 134-198):**
1. KYC fraud → `review_required` (confidence 0.95)
2. KYC missing docs → `review_required` (confidence 0.90)
3. High/Very_High credit → `deny` (confidence 0.85)
4. Policy fail + credit ≥ 700 → `review_required` (conflict, 0.80)
5. Policy fail + credit < 700 → `deny` (0.85)
6. Borderline credit 650-699 → `review_required` (0.70)
7. Weighted vote says not approve → `review_required` (tie-breaker, 0.72)
8. All clean → `approve` (unanimous, 0.95)

#### 19. `src/ui/app.py` — The API Gateway

**Purpose:** Serves the web frontend and REST API for the underwriting pipeline.

**Key functions:**
- `require_api_key()` (line 69) — Auth decorator
- `underwrite_application()` (line 163) — Runs graph.invoke(), stores result
- `submit_decision()` (line 196) — Applies human decision to stored state
- `_PIPELINE_STATE` (line 100) — In-memory store for pipeline results
- `_app_locks` (line 94) — Per-app threading locks for concurrent safety

**Code snippet worth memorizing — state desync prevention (lines 229-272):**

```python
with _app_locks[app_id]:
    if app_id not in _PIPELINE_STATE:
        return 400 "Pipeline must be run before decision"
    stored = _PIPELINE_STATE[app_id]
    if stored.get("final_status") in ("approved", "denied"):
        return 409 "Decision already submitted"
    previous_state = LoanApplicationState.from_dict(stored)
    previous_state.human_decision = HumanDecision(...)
    state_updates = human_review_node(previous_state)
    merged = previous_state.to_dict()
    merged.update(state_updates)
    _PIPELINE_STATE[app_id] = serialize_state(merged)
```

---

## 5. Testing Strategy

### Test Coverage Map

| Test File | Tests | What It Validates | Author |
|-----------|-------|-------------------|--------|
| `test_state.py` | 5 | Schema serialization, `@validate_state` decorator (success/failure) | **Purvansh** |
| `test_credit.py` | 26 | PRD formula, risk thresholds, confidence, KYC override, DTI guardrails | — |
| `test_kyc.py` | 6 | Missing docs, fraud (name mismatch), empty docs, low confidence, income mismatch | **Purvansh** |
| `test_policy.py` | 6 | Passed checks, failed DTI, failed employment, no documents | — |
| `test_arbitrator.py` | 8 | Unanimous approval, deny, conflict, fraud, review_required | — |
| `test_arbitrator_dummy.py` | 8 | Weighted vote unit tests, 6 end-to-end scenarios | — |
| `test_edges.py` | 8 | `route_after_kyc` (4 paths), `route_after_arbitrator` (always human_review) | — |
| `test_graph.py` | 5 | Happy path, human decision, fraud routing, full graph | — |
| `test_guardrails.py` | 7 | Input validation: missing data, insufficient docs, invalid types, size, audit logging | **Purvansh** |
| `test_output_validation.py` | × | (Covered by test_credit.py + test_integration.py) | — |
| `test_resilience.py` | 18 | Graceful fallbacks for all 4 agents, timeout enforcement | **Purvansh** |
| `test_document_tools.py` | 7 | PDF parsing, size limit, file type, document detection, field extraction | **Purvansh** |
| `test_human_review_tool.py` | 7 | Programmatic approve/deny/override, invalid decision, summary builder | — |
| `test_integration.py` | 14 | Full pipeline with mocks, PRD profiles, guardrail triggers, parametrized | — |
| `test_fraud_flag.py` | 10 | Fraud routing, fixture validation, audit logging | — |
| `test_observability.py` | 11 | LangSmith env vars, tracing enabled/disabled, trace_id, URL format | **Purvansh** |
| `test_api_security.py` | 32 | Malformed JSON, invalid decisions, empty officer_id, state desync, 409 | **Purvansh** |
| **Total** | **~190** | | **7 authored** |

### Testing Philosophy

1. **Mock-heavy for agent isolation** — `conftest.py` provides `mock_kyc_output`, `mock_policy_output_pass/fail`, `mock_arbitrator_*` fixtures. Integration tests mock KYC/Policy/Arbitrator and test only the real credit node.

2. **Parametrized tests** — `test_credit.py` and `test_integration.py` use `@pytest.mark.parametrize` to run the same assertion across multiple data profiles.

3. **State factories** — `make_application_state()` in `conftest.py` builds valid states with one call. Used extensively across test files.

4. **End-to-end tests** — `test_graph.py` runs `graph.invoke()` with real agent nodes (not mocked) to verify the full pipeline.

5. **Security tests** — `test_api_security.py` is the largest test file (32 tests). It tests edge cases: malformed JSON, null bytes, wrong content type, race conditions, state desync, and second-decision rejection (409).
6. **Observability tests** — `test_observability.py` tests LangSmith env var detection, tracing normalization (LANGSMITH_* → LANGCHAIN_* mirroring), and trace URL generation.
7. **Document tool tests** — `test_document_tools.py` tests PDF parsing, file size limits, file type validation, document type detection, and field extraction (LLM + regex fallback).

### Tricky Test Scenarios

**State desync (Bug-2):**

```python
# test_api_security.py:243-260
def test_decision_preserves_arbitrator_output(self, client):
    uw_data = _underwrite(client, "APP-002")
    arb_before = uw_data["arbitrator_output"]
    dec_resp = client.post("/api/decision/APP-002",
        json={"officer_id": "OFF-1", "decision": "deny"})
    dec_data = dec_resp.get_json()
    arb_after = dec_data["arbitrator_output"]
    assert arb_after == arb_before  # Must NOT change
```

This test verifies the bug fix: previously, the decision endpoint reloaded test data from `test_applications.json`, losing agent outputs. Now it uses `_PIPELINE_STATE`.

**Second decision rejection (409):**

```python
# test_api_security.py:374-388
def test_second_decision_overwrites_first(self, client):
    _underwrite(client, "APP-001")
    c1 = client.post("/api/decision/APP-001", ...)
    assert c1["final_status"] == "approved"
    c2 = client.post("/api/decision/APP-001", ...)
    assert c2.status_code == 409
```

**Timeout + fallback chain:**

```python
# test_resilience.py:106-118
def test_timeout_resilience_trigger():
    result = dummy_timeout_node(state)  # sleep 0.1s, timeout 0.05s
    assert result["credit_output"].credit_score == 300  # fallback values
    assert result["credit_output"].confidence_score == 0.0
```

---

## 6. Common Pitfalls & Debugging Guide

### Top 6 Things That Can Go Wrong

#### 1. ChromaDB Collection is Empty

**Symptom:** Policy agent returns no chunks; violations are "System error in policy checking."

**Root cause:** The `policy_docs/` directory is missing or the ChromaDB persistence directory was deleted. `_ensure_collection()` tries to auto-index, but if the markdown files aren't found, it raises.

**Debug:**
```bash
# Check if policy docs exist
ls data/policy_docs/*.md
# Should see: credit_policy.md dti_policy.md employment_policy.md ...

# Check if chroma_db has data
ls data/chroma_db/
# Should have collection files

# Force re-index: delete and restart
rm -rf data/chroma_db
python -c "from src.rag.policy_loader import load_and_index_policies; load_and_index_policies()"
```

#### 2. OpenAI API Key Not Set

**Symptom:** Document field extraction returns only regex-matched fields (limited accuracy). No error is thrown.

**Root cause:** `OPENAI_API_KEY` env var not set. `extract_fields()` checks `os.getenv("OPENAI_API_KEY")` and falls back to `extract_fields_fallback()`.

**Debug:**
```bash
echo $OPENAI_API_KEY  # Should not be empty
# Or check .env file
cat .env | grep OPENAI
```

**Fix:** Set `OPENAI_API_KEY` in `.env`. The system works without it, but field extraction quality degrades.

#### 3. LangSmith Trace Not Appearing

**Symptom:** `[trace] LangSmith tracing is OFF.` message when running `python -m src.main`.

**Root cause:** `LANGSMITH_TRACING` not set to `true`, or `LANGSMITH_API_KEY` is missing/invalid. The `_tracing_enabled()` function checks both `LANGSMITH_TRACING` and `LANGCHAIN_TRACING_V2`.

**Debug:**
```bash
# In Python:
import os; os.getenv("LANGSMITH_TRACING")  # Should be "true"
os.getenv("LANGSMITH_API_KEY")              # Should be set
```

**Fix:** Ensure `.env` has `LANGSMITH_TRACING=true` and a valid `LANGSMITH_API_KEY`.

#### 4. "No documents provided" Error on KYC

**Symptom:** `ValueError: Validation Error: No documents provided for application APP-XXX. Ingestion cannot proceed.`

**Root cause:** `state.documents` is empty when `kyc_node()` runs. This is INTENTIONAL — the guard raises an error when there are no documents.

**Debug:** Check the `build_state_from_app()` call. Is `app.get("documents", [])` empty? Is the `use_pdf_paths` flag causing issues?

**Note:** This is one of the errors that `graceful_fallback` deliberately propagates (doesn't catch). The system halts intentionally.

#### 5. Decision Endpoint Returns 400 "Pipeline must be run first"

**Symptom:** When submitting a decision via the API, you get a 400 error.

**Root cause:** The `/api/decision/<app_id>` endpoint checks `_PIPELINE_STATE`. If the pipeline hasn't been run for that app, there's nothing to decide on.

**Fix:** Hit `/api/underwrite/<app_id>` first. The frontend handles this automatically (Run Pipeline button before Submit Decision), but if you're calling the API directly, you must do both steps.

#### 6. Post-Merge RAG Breakage (embeddings + policy_tools)

**Commit fix:** `5c4ee71` — Resolved post-merge API breakage in policy retriever

**Symptom:** `RuntimeError: Policy retriever failed: ...` or ChromaDB returns empty results after merging branches.

**Root cause:** After merging separate branches (e.g., RAG from one branch, graph from another), the embeddings provider interface or policy retriever function signature may have diverged. Common issues:
- `get_embedding_provider()` wasn't properly imported (renamed to `get_embeddings()` and back)
- ChromaDB collection name mismatch between `policy_loader.py` and `policy_tools.py`
- `RetrievedPolicyChunk` class not updated to match retriever return format

**Debug:**
```bash
# Test RAG in isolation:
python -c "
from src.rag.embeddings import get_embeddings
e = get_embeddings()
print('Embeddings OK:', type(e).__name__)
from src.tools.policy_tools import policy_retriever
chunks = policy_retriever('minimum credit score')
print(f'Retrieved {len(chunks)} chunks')
for c in chunks[:2]:
    print(f'  [{c.score:.2f}] {c.text[:80]}...')
"
```

**Additional bugs fixed post-merge:**
| Bug | Commit | Symptom | Fix |
|-----|--------|---------|-----|
| LangSmith TypeError | `1a9f7ac` | `TypeError` in `get_run_url` call | Support both positional and keyword arg calling convention |
| Streamlift ModuleNotFound | `d29530d` | `ModuleNotFoundError` on `python -m streamlit run` | Add project root to `sys.path` |
| Empty ChromaDB collection | `33925df` | Policy agent returns no chunks silently | `_ensure_collection()` auto-indexes if count = 0 |
| Bypassed agent outputs | `00ec9b7` | `arbitrator_output` is None in retry/human_review nodes | `_populate_missing_agent_outputs()` runs skipped agents |

### Error Message Reference

| Error Message | Source | Meaning |
|--------------|--------|---------|
| `Input to {func} violates state schema` | `@validate_state` | Input dict missing required fields or has wrong types |
| `Output updates from {func} violate state schema` | `@validate_state` | Node's return dict has invalid fields |
| `Node '{func}' timed out after {seconds} seconds` | `@timeout_resilience` | Agent took too long (>30s) |
| `Error in node {func}: {detail}` | `@graceful_fallback` | Agent raised exception; fallback activated |
| `Validation Error: No documents provided` | `kyc_node` | Empty documents list |
| `File {path} exceeds maximum size limit of 10MB` | `parse_document` / `input_validation` | Document too large |
| `Invalid file type for {path}` | `parse_document` / `input_validation` | Not pdf/jpg/png/txt/md |
| `Policy retriever failed: {e}` | `policy_retriever` | ChromaDB query failed |
| `KYC Fraud Flagged (Document/Name mismatch)` | `arbitrator_node` | Fraud detected, appears in risk_flags |
| `Failed to parse PDF file at {path}` | `parse_pdf` | PyPDF2 failed (corrupted file?) |

### How to Trace a Request End-to-End

```bash
# 1. Start the Flask server
make run-demo
# Or: python src/ui/app.py
# Output: * Running on http://127.0.0.1:8501

# 2. Open http://127.0.0.1:8501 in browser
#    → Select APP-001 from the sidebar
#    → Click "Run Pipeline"

# 3. Server-side trace:
#    INFO riskpilot.app: Underwriting APP-001
#    INFO src.agents.kyc_agent: Starting KYC processing for APP-001
#    INFO src.agents.credit_agent: Starting credit risk assessment for APP-001
#    INFO src.agents.policy_agent: Starting policy compliance checking for APP-001
#    INFO src.graph.edges: Arbitration complete. Routing to HUMAN_REVIEW.
#    INFO riskpilot.app: Pipeline complete

# 4. Client-side inspection:
#    Open browser dev tools → Network tab
#    Watch POST /api/underwrite/APP-001 response
#    Response contains full LoanApplicationState as JSON

# 5. Decision flow:
#    Fill in officer decision form
#    POST /api/decision/APP-001 with body:
#    {
#        "officer_id": "OFF-001",
#        "decision": "approve"
#    }
#    Response: final_status = "approved"

# 6. Verify audit log:
cat logs/audit.jsonl | python -m json.tool | less

# 7. Verify LangSmith trace (if configured):
#    Check the printed URL in the server logs
```

### Debugging Strategy by Component

| Component | Debug Technique | Key File to Inspect |
|-----------|----------------|---------------------|
| KYC Agent | Add `state.applicant_data` and `state.documents` to logging | `kyc_agent.py`, `document_tools.py` |
| Credit Agent | Print intermediate values (income, dti, score, risk) | `credit_agent.py`, `credit_tools.py` |
| Policy Agent | Print `retrieved_chunks` to see RAG quality | `policy_agent.py`, `policy_tools.py` |
| Arbitrator | Print `kyc_lean`, `credit_lean`, `policy_lean`, `weighted_score` | `arbitrator_agent.py` |
| Graph | Use `graph.get_graph().draw_mermaid()` output | `graph.py`, `edges.py` |
| RAG | Query ChromaDB directly: `db.query(query_texts=["..."])` | `policy_loader.py`, `retriever.py` |
| Flask API | Check `_PIPELINE_STATE` content, verify locks | `app.py`, `app_config.py` |
| Tests | Use `pytest -vvs --log-cli-level=DEBUG` | Individual test files |

---

## 7. Enhancement Questions

### Q1: What if we added a 5th agent (e.g., a Collateral Agent)?

**To add a 5th agent to the graph:**

1. **Create the agent node** — `src/agents/collateral_agent.py` with `@validate_state @graceful_fallback("collateral") @timeout_resilience(30.0)`
2. **Add output model** — Add `CollateralOutput(SerializableModel)` to `src/graph/state.py`
3. **Add field to state** — Add `collateral_output: Optional[CollateralOutput] = None` to `LoanApplicationState`
4. **Add node to graph** — `builder.add_node("collateral", collateral_node)`
5. **Add edges** — Where should it run? Between Policy and Arbitrator is logical: `builder.add_edge("policy", "collateral")` then `builder.add_edge("collateral", "arbitrator")`
6. **Add lean signal** — In `arbitrator_node`, map collateral assessment to a lean score
7. **Add fallback** — Add `elif fallback_type == "collateral":` in `graceful_fallback`
8. **Add tests** — `test_collateral.py` with unit tests, update integration tests
9. **Update UI** — Add collateral results panel to `index.html`

**Tradeoffs:**
- More computation time (another LLM call, another ChromaDB query)
- More complex conflict resolution (4 agents instead of 3 in the weighted vote)
- Richer assessment (collateral valuation provides more information for the arbitrator)

### Q2: What if we switched from ChromaDB to Pinecone?

**Changes needed:**
1. Replace `src/rag/vector_store.py` — Swap `chromadb.Client` for `pinecone.Pinecone` client
2. Update `get_vector_store()` to return a Pinecone index instead of a ChromaDB collection
3. Change the query interface: `index.query(vector=embedding, top_k=3, include_metadata=True)`
4. Remove `MockCollection` fallback (Pinecone has no local mode, so use a local ChromaDB as dev fallback)
5. Add `PINECONE_API_KEY` and `PINECONE_ENVIRONMENT` to `.env.example`
6. Update `policy_loader.py` — Change upsert logic for Pinecone's namespace/index structure
7. Update `settings.yaml` — Change `vector_store` section

**Tradeoffs:**
- **Pros:** Pinecone scales horizontally, handles millions of vectors, has built-in namespaces, no local disk persistence to manage
- **Cons:** Network latency per query, requires API key, costs money, no offline mode
- **Dev/prod split:** Keep ChromaDB for development/testing, use Pinecone only in production

### Q3: What if we needed real-time streaming responses?

**Current state:** The LangGraph `graph.invoke()` is synchronous. The user clicks "Run Pipeline" and waits for a full response.

**To add streaming:**
1. Replace `graph.invoke()` with `graph.astream()` in `src/ui/app.py`
2. Flask's SSE or WebSocket: `Response(stream_with_context(generate()))` with `text/event-stream`
3. Each node completion emits an SSE event: `data: {"node": "kyc", "status": "complete"}\n\n`
4. Frontend: Use `EventSource` or fetch + ReadableStream to update UI progressively
5. Each agent result renders as it arrives, rather than all at once

**LangGraph's built-in approach:**
```python
# Instead of:
final_state = graph.invoke(state)

# Use:
for event in graph.astream(state):
    for node_name, output in event.items():
        yield f"data: {json.dumps({'node': node_name, 'output': serialize(output)})}\n\n"
```

**Tradeoffs:**
- Better UX (progressive rendering vs. blank loading)
- More complex connection management (SSE vs. WebSocket choice)
- Must handle mid-stream errors gracefully per node

### Q4: What if we scaled to 1000 concurrent users?

**Changes needed:**
1. **Replace in-memory state store** — `_PIPELINE_STATE` dict → Redis (or PostgreSQL)
2. **Replace in-memory rate limiting** — `flask-limiter` with `RATELIMIT_STORAGE_URI=redis://...`
3. **Replace ThreadPoolExecutor timeout** — For production, use `asyncio` with `asyncio.wait_for()` instead of `concurrent.futures`
4. **Add request queuing** — When 1000 concurrent invocations hit, queue them; don't create 1000 threads
5. **Stateless Flask** — Move to gunicorn with multiple workers; store session state in Redis
6. **Async LangGraph** — Use `graph.ainvoke()` (async) with an async HTTP server (uvicorn + FastAPI)
7. **Database for audit** — Replace JSONL audit with PostgreSQL + structured schema
8. **Connection pooling** — For ChromaDB/Pinecone, share a single client instance across requests

**Scaling bottlenecks:**
- **ChromaDB is single-node** — Consider Pinecone for vector search at scale
- **LLM rate limits** — Each request makes 4-8 LLM calls; 1000 concurrent = 4000-8000 concurrent LLM calls
- **Document parsing** — CPU-bound, consider a worker pool (Celery/RQ) for PDF processing
- **Thread safety** — Current `_app_locks` are per-process; with multiple workers, need distributed locks

### Q5: What if we integrated with a real loan origination system (LOS)?

**Integration points:**
1. **Input adapter** — Replace `data_loader.py` with an API client that fetches applications from the LOS
2. **Document retrieval** — Fetch documents from LOS document management via API (not file paths)
3. **Decision callback** — After human review, POST the decision back to the LOS via webhook
4. **Status sync** — Poll LOS for application status changes, update RiskPilot's view

**Architecture:**
```
LOS API → Input Adapter → RiskPilot Pipeline → Decision Callback → LOS Webhook
            └─> Maps LOS fields to  ──>   └─> Maps RiskPilot fields back
               LoanApplicationState
```

**New concerns:**
- Idempotency (don't process the same application twice)
- Error handling (LOS API down → retry queue)
- Data privacy (PII handling, encryption in transit and at rest)

### Q6: What if we needed to support multiple languages?

**Changes needed:**
1. **OCR** — pytesseract supports multiple languages with `lang='eng+fra+deu'`
2. **Field extraction** — Update LLM prompt to specify the language of extracted text
3. **Policy docs** — Translate (or maintain parallel) policy documents per language
4. **Policy retrieval** — ChromaDB embeddings are language-agnostic if using multilingual embeddings (e.g., `intfloat/multilingual-e5-base` instead of `BAAI/bge-small-en-v1.5`)
5. **UI** — `index.html` with i18n (e.g., `data-i18n` attributes + language JSON files)

**Multilingual embeddings:**
```python
# Switch from BGE to multilingual:
# config/settings.yaml
embeddings:
  model_name: "intfloat/multilingual-e5-base"  # Supports 100+ languages
```

### Q7: What if a loan officer needs to upload documents not just select test cases?

**Changes needed:**
1. **File upload endpoint** — `POST /api/upload` accepting multipart/form-data
2. **Dynamic state creation** — Create `LoanApplicationState` with uploaded files, no `test_applications.json` dependency
3. **Form for applicant data** — Add fields to `index.html` for name, income, debt, loan amount, property value, employment months
4. **Validation** — Run input guardrails on the form data
5. **Session management** — Store per-officer session with application history

**New endpoint:**
```python
@app.route("/api/upload", methods=["POST"])
@require_api_key
def upload_application():
    # Parse form data for applicant info
    applicant_data = {
        "name": request.form["name"],
        "income": float(request.form["income"]),
        ...
    }
    # Parse uploaded files
    documents = []
    for f in request.files.getlist("documents"):
        doc_type = detect_document_type(f.filename)
        # Save to temp dir, add as ExtractedDocument
        save_path = f"/tmp/{uuid.uuid4()}_{f.filename}"
        f.save(save_path)
        documents.append(ExtractedDocument(
            document_type=doc_type,
            extracted_text=save_path,  # Will be parsed by KYC
            validation_status="pending",
            confidence=0.0,
            extracted_fields={},
        ))
    state = LoanApplicationState(
        application_id=f"APP-{uuid.uuid4().hex[:8].upper()}",
        applicant_data=applicant_data,
        documents=documents,
    )
    # Run pipeline
    result = graph.invoke(state)
    return jsonify(serialize(result))
```

### Q8: What if we wanted to A/B test different credit scoring models?

**Design:**
1. **ScoreModelStrategy interface** — Abstract base class for scoring models
2. **Current model** — `PRDScoreModel()` implementing the existing formula
3. **New model** — `MLScoreModel()` using a pre-trained regression model (e.g., XGBoost)
4. **Scoring model factory** — `get_score_model(model_name)` in `credit_tools.py`
5. **Configuration** — `settings.yaml`: `model.credit_scoring: "PRD"` or `model.credit_scoring: "ML"`
6. **A/B test framework** — Run both models, log both outputs, compare accuracy against known outcomes

**Implementation sketch:**
```python
class PRDScoreModel:
    def calculate(self, income, monthly_debt, employment_months):
        dti = monthly_debt / max(1, income/12)
        return 300 + (income/1000)*10 + employment_months*2 - dti*200

class MLScoreModel:
    def __init__(self):
        self.model = joblib.load("models/xgb_credit_score.pkl")
    def calculate(self, income, monthly_debt, employment_months):
        features = [[income, monthly_debt, employment_months]]
        return int(self.model.predict(features)[0])

# In credit_agent.py:
from config import settings
model = PRDScoreModel() if settings.model.credit_scoring == "PRD" else MLScoreModel()
credit_score = model.calculate(income, monthly_debt, employment_months)
```

### Q9: What if we needed to comply with ECOA/Fair Lending regulations?

**ECOA (Equal Credit Opportunity Act)** prohibits discrimination based on race, color, religion, national origin, sex, marital status, age, or public assistance.

**To comply:**
1. **Remove protected attributes** — Ensure the state schema and applicant data NEVER include protected attributes. If they come in via documents, strip them before the credit agent.
2. **Adverse action notice** — When an application is denied, generate an `AdverseActionNotice` with specific reasons (violations from policy agent).
3. **Disparate impact testing** — Run the pipeline against synthetic demographic data to check for statistically significant differences in approval rates.
4. **Audit trail** — The existing `audit.jsonl` satisfies the record-keeping requirement. Ensure it includes reason codes.
5. **Override documentation** — When an officer overrides a recommendation, the reason must be documented (already required by `human_review_tool.py`).

**For the arbitrator, ensure fairness:**
```python
# In arbitration, use ONLY financial factors, never demographic:
# ✅ ACCEPTABLE: credit_score, dti_ratio, ltv_ratio, employment_months
# ❌ NOT ACCEPTABLE: race, gender, age, zip_code, marital_status
```

### Q10: What if a node produces conflicting outputs (e.g., KYC says name is "John", pay slip says "Jonathan")?

**Current handling:** The KYC agent detects name mismatch and sets `fraud_flag = True`. The arbitrator sees this and routes to `review_required`.

**Enhanced handling if needed:**
1. **Confidence-weighted name resolution** — Not just fraud flag, but pick the name from the highest-confidence document
2. **Field-level confidence** — Each extracted field gets its own confidence score, not document-level
3. **Majority vote** — If 3 documents say "John Doe" and 1 says "Jonathan Doe", use the majority
4. **Human review flag** — Mark specific fields as requiring human verification, not the whole application

---

## 8. Interview Prep Section

### Key Terminology

| Term | Definition |
|------|------------|
| **LangGraph** | A framework from LangChain for building stateful, multi-agent applications as directed graphs |
| **DAG** | Directed Acyclic Graph — the graph topology where edges flow in one direction with no cycles |
| **Node** | A function in the LangGraph that processes state and returns updates |
| **Edge** | A connection between nodes; can be static (always A→B) or conditional (A→B, C, or D based on state) |
| **State** | A typed Pydantic object (`LoanApplicationState`) that flows through the graph |
| **RAG** | Retrieval-Augmented Generation — querying a vector database for relevant documents, then using them to inform decisions |
| **ChromaDB** | An open-source vector database; stores policy document embeddings locally |
| **BGE Embeddings** | BAAI General Embedding — a family of embedding models (`bge-small-en-v1.5` used here) |
| **HITL** | Human-In-The-Loop — mandatory human review before any final decision |
| **DTI** | Debt-to-Income ratio: monthly debt payments / monthly income |
| **LTV** | Loan-to-Value ratio: loan amount / property value |
| **PRD** | Product Requirements Document — the specification that defined the scoring formula and thresholds |
| **Guardrails** | Safety checks that validate inputs and outputs, preventing the system from producing invalid or unsafe results |
| **Weighted Voting** | A mechanism where each agent's recommendation is multiplied by its confidence, summed, and normalized to produce a final score |
| **LangSmith** | An observability platform for LLM applications; traces every node execution |
| **`@graceful_fallback`** | Decorator that catches agent failures and returns safe default values |
| **`@timeout_resilience`** | Decorator that kills agent execution if it exceeds a time limit |
| **`@validate_state`** | Decorator that ensures schema compliance on every node's input and output |

### Architecture Tradeoff Discussion Points

**Why Pydantic vs. TypedDict?**
- Pydantic provides validation, serialization, and type coercion
- TypedDict is lighter but offers no runtime validation
- Tradeoff: Pydantic's `ValidationError` vs. TypedDict's silent type violations

**Why LangGraph vs. monolithic agent?**
- Pros: Separation of concerns, testability, replaceability, traceability
- Cons: More boilerplate, more files, slightly more complex data flow
- When monolithic wins: Simple single-step tasks with no branching

**Why ChromaDB vs. Pinecone/Weaviate?**
- ChromaDB: Local, free, zero configuration, good for development and moderate scale
- Pinecone: Managed, scalable, good for production
- Tradeoff: Operational simplicity vs. scalability

**Why Flask vs. FastAPI?**
- Flask: Simpler, more libraries, better for single-page apps
- FastAPI: Async, auto-docs, better for API-only services
- RiskPilot uses Flask because the frontend is server-rendered HTML, not a separate SPA

**Why ThreadPoolExecutor vs. asyncio for timeouts?**
- ThreadPoolExecutor: Works with synchronous code, simpler to integrate
- asyncio: More efficient, better for I/O-bound tasks, but requires async-everywhere
- Tradeoff: Thread overhead vs. async complexity

**Why in-memory state vs. database?**
- In-memory: Simple, fast, lost on restart
- Database: Persistent, shared across workers, requires connection management
- Current choice is appropriate for a demo; a production system would need a database

### "Tell Me About a Challenge You Faced" Prompts

**Challenge 1: State Desync (Bug-2)**

*What happened:* The decision endpoint was reloading test data from `test_applications.json` instead of using the stored pipeline output. This meant agent outputs (especially `arbitrator_output`) could be different between the pipeline run and the decision.

*How I fixed it:* Changed the Flask API to store the full pipeline output in `_PIPELINE_STATE` dict (keyed by app_id). The decision endpoint reads from this stored state, applies the `human_decision`, and re-runs only the `human_review_node` — not the entire pipeline.

*What I learned:* Never assume two calls to the same function return identical results, especially when RAG and LLM calls are involved. Always cache deterministic pipeline outputs.

**Challenge 2: Decorator Order (Resilience Chain)**

*What happened:* Initially, `@graceful_fallback` didn't catch `TimeoutError` from `@timeout_resilience` because the decorator order was wrong.

*How I fixed it:* Applied decorators in the correct order: `@validate_state` (outermost) → `@graceful_fallback` (middle) → `@timeout_resilience` (innermost). This ensures the call chain is:
1. Validate input
2. Try/except (fallback)
3. Timeout wrapper
4. Real function

*What I learned:* Decorator order matters critically. The execution order is innermost-to-outermost, but the stack order is outermost-to-innermost.

**Challenge 3: PDF Parsing Reliability**

*What happened:* Synthetic PDFs generated by reportlab sometimes produced unparseable output from PyPDF2. Empty pages, encoding issues.

*How I fixed it:* Added `@timeout_resilience(30.0)` to `parse_document()` to prevent hangs. Added the LLM + regex dual-extraction approach so even if PyPDF2 output is garbled, the regex can still find key fields like name and income.

*What I learned:* In production document processing, always assume input is malformed. Layer multiple extraction strategies: LLM → regex → default fallback.

### Explaining the System to Non-Technical Stakeholders

**Elevator pitch (30 seconds):**

> "RiskPilot is like having four specialist underwriters work on a loan application simultaneously. One checks identity documents, one calculates financial ratios, one looks up company policies, and one weighs all the evidence to make a recommendation. But they don't make the final call — a human loan officer always reviews their work before any decision reaches the customer."

**One minute:**

> "When a loan application comes in, RiskPilot first validates the data — making sure all required fields and documents are present. Then it runs through four automated checks: identity verification, credit assessment, policy compliance, and arbitration. Each check is handled by a specialized AI agent. The system is transparent — you can see exactly what each agent found. Finally, a human loan officer reviews everything and makes the final decision. Every single step is logged for audit and compliance purposes."

**Deep dive for managers:**

> "The system uses a technology called LangGraph, which lets us chain AI agents together in a controlled pipeline. Each agent has a single job: the KYC agent reads documents, the credit agent calculates risk, the policy agent checks rules, and the arbitrator resolves conflicts. They all share a common data structure so nothing gets lost. The entire system is wrapped in safety guards — validation on inputs, fallback plans if any agent fails, time limits on processing, and mandatory human review before any final decision. We have 155 automated tests ensuring everything works correctly."

---

## 9. Self-Assessment Checklist

### Core Understanding

- [ ] I can explain the entire flow from upload to decision in under 2 minutes
- [ ] I can describe each agent's responsibility in one sentence
- [ ] I understand how state is managed through the graph
- [ ] I know where timeouts are applied and why (30s per agent + parse/extract)
- [ ] I can explain the RAG implementation (ChromaDB + BGE embeddings)
- [ ] I understand the security model (API keys, CORS, rate limits, state locks)
- [ ] I can trace a bug through the system (from symptom to root cause)
- [ ] I know how to add a new agent to the graph
- [ ] I understand the UI/backend separation (Flask API ↔ index.html SPA)
- [ ] I can run and debug the full application

### Decorators & Resilience

- [ ] I can explain the execution order: `@validate_state` → `@graceful_fallback` → `@timeout_resilience`
- [ ] I know what `@validate_state` validates (input schema + output schema)
- [ ] I know what `@graceful_fallback` catches and what it propagates
- [ ] I know what `@timeout_resilience` does and its default timeout
- [ ] I know the fallback values for each agent type
- [ ] I understand why certain errors (Validation Error, No documents) are propagated

### Architecture & Design

- [ ] I can draw the LangGraph topology from memory
- [ ] I can explain the conditional routing logic (KYC → credit/retry/review)
- [ ] I understand the weighted voting formula: `Σ(c_i × lean_i) / Σ(c_i)`
- [ ] I know the PRD credit score formula and risk thresholds
- [ ] I know the policy validation thresholds (min 650 credit, 45% DTI, 80% LTV, 12mo emp)
- [ ] I understand the arbitrator conflict detection rules
- [ ] I know how the Flask API stores and protects state (`_PIPELINE_STATE` + per-app locks)
- [ ] I understand the state desync bug fix (Bug-2)

### Code Knowledge

- [ ] I can locate and explain every file in `src/`
- [ ] I can write a new agent node following the established pattern
- [ ] I can add a new test application to `test_applications.json`
- [ ] I can modify the graph topology safely
- [ ] I can debug a failing test by reading the error and tracing through code
- [ ] I can explain the `SerializableModel` base class and why it exists

### Testing & Operations

- [ ] I can run all tests with `make test`
- [ ] I can run a specific test file or single test
- [ ] I can launch the Flask app and test endpoints via curl
- [ ] I can check the audit log at `logs/audit.jsonl`
- [ ] I can verify LangSmith traces are working
- [ ] I know how to force re-index the RAG collection

### If I answered "No" to any of these:

Go back to the relevant section of this guide, read the code, run the tests, and experiment with the application until you can say "Yes."

---

## 10. Quick Reference Cards

### Quick Reference 1: Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `OPENAI_API_KEY` | No | — | GPT-4o-mini for field extraction (fallback: regex) |
| `LANGSMITH_TRACING` | No | — | Enable LangSmith tracing (`true`/`false`) |
| `LANGSMITH_API_KEY` | No | — | LangSmith API key |
| `LANGSMITH_PROJECT` | No | RiskPilot | LangSmith project name |
| `LANGSMITH_ENDPOINT` | No | https://api.smith.langchain.com | LangSmith endpoint |
| `DEBUG` | No | false | Flask debug mode |
| `HOST` | No | 127.0.0.1 | Flask bind address |
| `PORT` | No | 8501 | Flask port |
| `SECRET_KEY` | No | random hex | Flask session key |
| `ALLOWED_ORIGIN` | No | "" | CORS allowed origin |
| `MAX_CONTENT_LENGTH` | No | 1048576 (1MB) | Request body size limit |
| `API_KEYS` | No | "" | Comma-sep API keys (empty = auth disabled) |
| `RISKPILOT_AUDIT_LOG` | No | logs/audit.jsonl | Audit log path |

### Quick Reference 2: Main API Endpoints

| Method | Path | Auth | Rate Limit | Request Body | Response |
|--------|------|------|------------|--------------|----------|
| GET | `/api/applications` | Optional | 200/day, 50/hour | — | JSON array of applications |
| POST | `/api/underwrite/<app_id>` | Optional | 200/day, 50/hour | `{"fast_mode": bool}` | Full state JSON |
| POST | `/api/decision/<app_id>` | Optional | **10/minute** | `{"officer_id": str, "decision": str, "override_reason": str?}` | Full state JSON with final_status |

**Decision values:** `approve`, `deny`, `override_approve`, `override_deny`

**HTTP status codes:**
- 200 — Success
- 400 — Bad request (malformed JSON, missing fields, pipeline not run)
- 401 — Missing/invalid API key
- 404 — Application not found
- 409 — Decision already submitted (second attempt blocked)
- 500 — Internal server error

### Quick Reference 3: State Schema Fields

```yaml
LoanApplicationState:
  application_id: str                          # Unique ID (e.g., "APP-001")
  trace_id: Optional[str]                      # LangSmith trace UUID
  applicant_data: Dict[str, Any]               # {name, income, monthly_debt, loan_amount, property_value, employment_months}
  documents: List[ExtractedDocument]           # Parsed documents with fields

  # Agent outputs (populated sequentially)
  kyc_output: Optional[Dict[str, Any]]         # {status, missing_critical_docs, fraud_flag, confidence, verified_fields}
  credit_output: Optional[CreditRiskOutput]    # {credit_score (300-850), risk_category, dti_ratio, default_probability, confidence_score, reasoning}
  policy_output: Optional[PolicyCheckOutput]    # {policy_passed, violations[], ltv_ratio, min_credit_requirement_met, max_dti_threshold, retrieved_policy_chunks[], reasoning}
  arbitrator_output: Optional[ArbitratorOutput] # {recommendation (approve/deny/review_required), confidence_score, agent_agreement (unanimous/partial/conflict), summary, risk_flags[]}

  # Decision
  human_decision: Optional[HumanDecision]      # {officer_id, decision, override_reason?, timestamp}
  final_status: Optional[Literal]              # "approved" | "denied" | "under_review"

  # Audit
  error_log: List[str]                         # Errors from agent nodes
  state_version: str = "1.0.0"                 # Schema version
  updated_at: Optional[str]                    # ISO-8601 timestamp
```

### Quick Reference 4: Agent Node Functions

| Function | File | Decorators | Input | Output Keys | Fallback Behavior |
|----------|------|------------|-------|-------------|-------------------|
| `kyc_node` | `kyc_agent.py` | `@validate_state @graceful_fallback("kyc") @timeout_resilience(30.0)` | State with docs | `kyc_output`, `documents`, `error_log` | `status=failed, missing_docs=[all], confidence=0.0` |
| `credit_node` | `credit_agent.py` | `@validate_state @graceful_fallback("credit") @timeout_resilience(30.0)` | State (needs KYC) | `credit_output`, `error_log` | `score=300, risk=very_high, dti=1.0, confidence=0.0` |
| `policy_node` | `policy_agent.py` | `@validate_state @graceful_fallback("policy") @timeout_resilience(30.0)` | State (needs Credit) | `policy_output`, `error_log` | `passed=False, violations=["System error"]` |
| `arbitrator_node` | `arbitrator_agent.py` | `@validate_state @graceful_fallback("arbitrator") @timeout_resilience(30.0)` | State (needs Policy) | `arbitrator_output`, `error_log` | `recommendation=review_required, confidence=0.0, conflict` |
| `retry_node` | `graph.py` | `@validate_state` | State (missing docs) | `final_status`, `error_log`, agent outputs | — |
| `human_review_node` | `graph.py` | `@validate_state` | State (any) | `final_status`, `error_log` | — |

### Quick Reference 5: Resilience Decorators

**`@validate_state`** — `src/graph/state.py:128`
```python
def validate_state(func):
    # 1. Validate input is LoanApplicationState or valid dict
    # 2. Run func
    # 3. Validate output dict merges cleanly into state
    # 4. Stamp updated_at
```

**`@timeout_resilience(seconds=30.0)`** — `src/graph/state.py:175`
```python
def timeout_resilience(seconds=30.0):
    # Runs func in ThreadPoolExecutor
    # future.result(timeout=seconds) → TimeoutError if exceeded
```

**`@graceful_fallback(fallback_type)`** — `src/graph/state.py:198`
```python
def graceful_fallback(fallback_type):
    # Try: return func(state)
    # Except:
    #   - Propagate "Validation Error" and "No documents"
    #   - Log to error_log
    #   - Return fallback dict per fallback_type:
    #     "kyc" → kyc_output with status=failed, confidence=0.0
    #     "credit" → CreditRiskOutput score=300, dti=1.0, confidence=0.0
    #     "policy" → PolicyCheckOutput passed=False
    #     "arbitrator" → ArbitratorOutput review_required
```

**Execution order (inner to outer):**
```python
@validate_state          # 4. Validate output schema (and input)
@graceful_fallback("x")  # 3. Catch exceptions, return fallback
@timeout_resilience(30)  # 2. Enforce time limit
def agent_node(state):   # 1. Real work
```

---

> **End of Study Guide**
>
> Created for Purvansh — RiskPilot Project  
> Last updated: June 2026  
> Based on 36 commits across 100+ files | 7 test files authored
