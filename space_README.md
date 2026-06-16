---
title: Ollive OSS Assistant
emoji: "🫒"
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 4.x
app_file: space_app.py
pinned: false
license: mit
---

# Ollive OSS Assistant

A lightweight open-source AI personal assistant built on `Qwen2.5-0.5B-Instruct` — part of the [Ollive Intelligent AI Gateway](https://github.com/anomalyco/ollive-assistant).

## Features

- Multi-turn conversational memory over the last 10 turns
- Local Llama Guard 3 safety guardrails (14 harm categories)
- Calculator tool support
- Optional Langfuse observability tracing
- File parsing (PDF, CSV, TXT)

## Running Locally

```bash
pip install -r requirements.txt
python space_app.py
```

For the full gateway with frontier model routing, evaluation suite, admin dashboard, and Docker deployment, see the [main repository](https://github.com/anomalyco/ollive-assistant).
