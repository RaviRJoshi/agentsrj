"""A minimal, framework-free AI agent with function calling.

The agent talks to the OpenAI Chat Completions API directly and runs a
manual tool-call loop. It exposes three tools:

1. record_email   - save an email to a local log file
2. add_numbers    - add two numbers
3. geography_lookup - answer geography questions from a small dataset

Run it directly:
    python agent.py

Or ask a single question non-interactively:
    python agent.py "What is the capital of Japan and what is 12 + 30?"
"""

from __future__ import annotations

import json
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

from tool_schemas import TOOLS, tool_map

load_dotenv(override=True)

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4")

SYSTEM_PROMPT = (
    "You are a helpful assistant with access to tools. "
    "Use record_email when the user wants to save an email, add_numbers for "
    "arithmetic, and are a Geography Ninja who knnows everything about geography. "
    "Always use the tools rather than answering from memory when one fits, "
    "and briefly confirm what you did after a tool call."
)


def run_tool(name: str, arguments: dict):
    """Dispatch a tool call to the matching Python function."""
    func = tool_map()[name]
    return func(**arguments)


def chat(client: OpenAI, messages: list[dict]) -> str:
    """Run the agent loop: call the model, execute any tools, repeat."""
    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
        )
        message = response.choices[0].message

        # No tool calls requested -> we are done.
        if not message.tool_calls: return message.content or ""

        # Record the assistant's tool-call turn, then run each tool.
        messages.append(message)
        for call in message.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            try:
                result = run_tool(call.function.name, args)
            except Exception as exc:  # surface errors back to the model
                result = f"Error calling {call.function.name}: {exc}"
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": str(result),
                }
            )
        # Loop again so the model can read tool results and answer.


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY not set. Copy .env.example to .env and add your key.")

    client = OpenAI()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Single-shot mode: pass a question as the first CLI argument.
    if len(sys.argv) > 1:
        messages.append({"role": "user", "content": " ".join(sys.argv[1:])})
        print(chat(client, messages))
        return

    # Interactive chat mode.
    print("Agent ready. Type your message (ctrl-d or 'exit' to quit).")
    while True:
        try:
            user = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user or user.lower() in {"exit", "quit"}:
            break
        messages.append({"role": "user", "content": user})
        reply = chat(client, messages)
        messages.append({"role": "assistant", "content": reply})
        print(f"agent> {reply}")


if __name__ == "__main__":
    main()