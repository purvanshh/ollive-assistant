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

A lightweight open-source AI personal assistant built on `Qwen2.5-0.5B-Instruct`.

## Features

- Multi-turn conversational memory over the last 10 turns
- Safety guardrails with a keyword blocklist
- Calculator tool support
- Optional observability via Langfuse

## Running Locally

```bash
pip install -r requirements.txt
python space_app.py
```
