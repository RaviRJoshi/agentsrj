# 10_foudations — Function-Calling Agent

A minimal, framework-free AI agent that uses the OpenAI Chat Completions
API directly with a manual tool-call loop.

## Tools

1. `record_email(sender, subject, body)` — appends an email to `emails_log.txt`.
2. `add_numbers(a, b)` — returns the sum of two numbers.
3. `geography_lookup(place)` — returns capital / continent / population from
   a small built-in dataset, so the LLM acts as a geography scholar without
   relying on its own memory.

## Setup

```bash
cp .env.example .env      # then paste your OpenAI key into .env
```

`OPENAI_API_KEY` is required; `OPENAI_MODEL` defaults to `gpt-5.4-mini`.

## Run

```bash
# Interactive chat
python agent.py

# One-shot question
python agent.py "What is the capital of Japan and what is 12 + 30?"
```

## Files

- `agent.py` — entry point, conversation loop, tool dispatch.
- `tool_schemas.py` — JSON tool schemas sent to the model + name→function map.
- `tools.py` — the actual Python functions.
- `emails_log.txt` — created on first `record_email` call (gitignored).