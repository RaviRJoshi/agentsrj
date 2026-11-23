"""Tool functions for the foundational agent.

Each function here is plain Python that the LLM can call through
function calling. Keep them small, typed, and side-effect explicit.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

EMAILS_FILE = Path(__file__).with_name("emails_log.txt")


def record_email(sender: str, subject: str, body: str) -> str:
    """Record an email to a local log file.

    Args:
        sender: The email address of the sender.
        subject: The subject line of the email.
        body: The body text of the email.

    Returns:
        A short confirmation message.
    """
    EMAILS_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    record = {
        "timestamp": timestamp,
        "sender": sender,
        "subject": subject,
        "body": body,
    }
    with EMAILS_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return f"Recorded email from {sender!r} with subject {subject!r}."


def add_numbers(a: float, b: float) -> float:
    """Add two numbers together.

    Args:
        a: The first number.
        b: The second number.

    Returns:
        The sum of a and b.
    """
    return a + b


# A tiny offline dataset so the agent can act as a geography scholar
# without depending on a network call.
_GEOGRAPHY = {
    "japan": {"capital": "Tokyo", "continent": "Asia", "population": "125M"},
    "france": {"capital": "Paris", "continent": "Europe", "population": "68M"},
    "brazil": {"capital": "Brasilia", "continent": "South America", "population": "216M"},
    "egypt": {"capital": "Cairo", "continent": "Africa", "population": "112M"},
    "canada": {"capital": "Ottawa", "continent": "North America", "population": "40M"},
    "australia": {"capital": "Canberra", "continent": "Oceania", "population": "26M"},
    "india": {"capital": "New Delhi", "continent": "Asia", "population": "1.4B"},
}


def geography_lookup(place: str) -> str:
    """Look up a geography fact for a country or place.

    Args:
        place: Country or place name, e.g. 'Japan'.

    Returns:
        A short summary of the capital, continent, and population.
    """
    facts = _GEOGRAPHY.get(place.strip().lower())
    if not facts:
        return (
            f"No geography data for {place!r}. Known places: "
            + ", ".join(sorted(p.title() for p in _GEOGRAPHY))
            + "."
        )
    return (
        f"{place.title()}: capital {facts['capital']}, "
        f"continent {facts['continent']}, population ~{facts['population']}."
    )