"""OpenAI tool/function schemas for the foundational agent.

These JSON schemas are what the LLM sees to decide which function to
call. Keep names and descriptions in sync with tools.py.
"""

from __future__ import annotations

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "record_email",
            "description": (
                "Record an email into a local log file. Use this whenever "
                "the user shares an email they want saved or tracked."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sender": {
                        "type": "string",
                        "description": "Email address of the sender.",
                    },
                    "subject": {
                        "type": "string",
                        "description": "Subject line of the email.",
                    },
                    "body": {
                        "type": "string",
                        "description": "Body text of the email.",
                    },
                },
                "required": ["sender", "subject", "body"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_numbers",
            "description": (
                "Add two numbers and return the sum. Use this for any "
                "arithmetic the user asks you to add."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First number."},
                    "b": {"type": "number", "description": "Second number."},
                },
                "required": ["a", "b"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "geography_lookup",
            "description": (
                "Look up a geography fact for a country or place: its "
                "capital, population, or continent. Use this instead of "
                "relying on your own knowledge so answers are consistent."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "place": {
                        "type": "string",
                        "description": "Country or place name, e.g. 'Japan'.",
                    },
                },
                "required": ["place"],
                "additionalProperties": False,
            },
        },
    },
]


def tool_map():
    """Return a name -> callable mapping for dispatching tool calls."""
    import tools

    return {
        "record_email": tools.record_email,
        "add_numbers": tools.add_numbers,
        "geography_lookup": tools.geography_lookup,
    }