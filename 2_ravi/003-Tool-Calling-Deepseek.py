# 003_LLM-Orchestration-agent-refactored.py
"""
Refactored order-processing agent.

Improvements over the original:
  1. Business rule (10% discount only above 1000) enforced in CODE, not just prompt.
  2. Tools return structured dicts; the confirmation tool verifies the final amount.
  3. Agent is a class -> no module-level mutable history, safe for multiple calls.
  4. Deterministic sampling (temperature=0) and a real model name.
  5. Single registry drives both the tool schemas and the dispatch table.
  6. Robust tool execution with validation and structured error results.
  7. Logging instead of print; failures surface cleanly.
  8. Test matrix exercises the "discount", "no-discount", and "not found" paths.
"""

import json
import logging
from typing import Any, Callable

from dotenv import load_dotenv
from openai import APIError, OpenAI

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# Use a real, currently-available model. gpt-4o-mini is cheap and reliable
# for function-calling experiments. Swap for gpt-4o if you need more reasoning.
MODEL = "gpt-4o-mini"

DISCOUNT_THRESHOLD = 1000.0
DISCOUNT_RATE = 0.10

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)

# override=False (the default) means an OPENAI_API_KEY already set in your
# shell wins over the .env file. Flip to True only if you deliberately want
# .env to clobber the environment.
load_dotenv(override=False)

# ---------------------------------------------------------------------------
# Simulated data / business logic
# ---------------------------------------------------------------------------

ORDERS: dict[str, float] = {
    "ORD101": 2000,
    "ORD102": 500,
    "ORD103": 1500,
}

def get_order_details_tool(order_id: str) -> dict[str, Any]:
    """Return {order_id, amount} on success, or {error} if not found."""
    if order_id not in ORDERS:
        return {"error": f"Order {order_id} not found"}
    return {"order_id": order_id, "amount": ORDERS[order_id]}

def calculate_discount_tool(amount: float) -> dict[str, Any]:
    """
    Return the discount amount. The threshold rule lives HERE, in code,
    so the model cannot talk us into discounting a small order.
    """
    if amount > DISCOUNT_THRESHOLD:
        discount = round(amount * DISCOUNT_RATE, 2)
        return {"discount": discount, "applied": True, "threshold": DISCOUNT_THRESHOLD}
    return {"discount": 0.0, "applied": False, "threshold": DISCOUNT_THRESHOLD}

def send_order_confirmation_tool(order_id: str, final_amount: float) -> dict[str, Any]:
    """
    Send the confirmation, but first verify the final_amount against our
    source of truth. If the model did the arithmetic wrong, we reject
    instead of emailing a bogus number.
    """
    if order_id not in ORDERS:
        return {"error": f"Cannot confirm unknown order {order_id}"}

    amount = ORDERS[order_id]
    expected = round(amount - (amount * DISCOUNT_RATE if amount > DISCOUNT_THRESHOLD else 0), 2)
    if round(final_amount, 2) != expected:
        return {
            "error": "Final amount mismatch",
            "expected": expected,
            "received": final_amount,
        }

    log.info("Confirmation sent | order=%s final_amount=%s", order_id, final_amount)
    return {"sent": True, "order_id": order_id, "final_amount": final_amount}

# ---------------------------------------------------------------------------
# Tool registry
# One entry per tool: (callable, json_schema). TOOLS and the dispatch
# table are both derived from this, so they can never drift apart.
# ---------------------------------------------------------------------------

TOOL_REGISTRY: dict[str, tuple[Callable[..., Any], dict[str, Any]]] = {
    "get_order_details_tool": (
        get_order_details_tool,
        {
            "type": "function",
            "function": {
                "name": "get_order_details_tool",
                "description": (
                    "Retrieve order details for an order ID. "
                    "Returns {order_id, amount} on success, or {error} if not found."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {"order_id": {"type": "string"}},
                    "required": ["order_id"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        },
    ),
    "calculate_discount_tool": (
        calculate_discount_tool,
        {
            "type": "function",
            "function": {
                "name": "calculate_discount_tool",
                "description": (
                    "Compute the discount for an order amount. "
                    "Applies 10% only when amount > 1000; otherwise returns 0."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {"amount": {"type": "number"}},
                    "required": ["amount"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        },
    ),
    "send_order_confirmation_tool": (
        send_order_confirmation_tool,
        {
            "type": "function",
            "function": {
                "name": "send_order_confirmation_tool",
                "description": (
                    "Send an order confirmation for an order ID and the final amount "
                    "after discount. The tool verifies the amount against the order record."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string"},
                        "final_amount": {"type": "number"},
                    },
                    "required": ["order_id", "final_amount"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        },
    ),
}

TOOLS = [schema for _, schema in TOOL_REGISTRY.values()]
FUNCTIONS = {name: fn for name, (fn, _) in TOOL_REGISTRY.items()}

# ---------------------------------------------------------------------------
# System prompt
# Note: the business rule is stated here as a HINT, but it's enforced in code.
# The prompt no longer needs to spell out a step-by-step algorithm; the model
# can infer the workflow from the tool descriptions.
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an order processing assistant.

Available tools:
1. get_order_details_tool(order_id) -> {order_id, amount} or {error}
2. calculate_discount_tool(amount)   -> {discount, applied}
3. send_order_confirmation_tool(order_id, final_amount) -> {sent, ...} or {error}

Workflow:
- Look up the order first.
- If not found, report that fact and stop.
- Otherwise calculate the discount, compute the final amount as
  amount - discount, and send the confirmation.
- Report the order details, discount, and final amount to the user.

Never invent order amounts. Only call calculate_discount_tool on amounts
you obtained from get_order_details_tool.
"""

# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class OrderAgent:
    """Encapsulates history so multiple agents / calls don't share state."""

    def __init__(self, model: str = MODEL, max_iterations: int = 10):
        self.client = OpenAI()
        self.model = model
        self.max_iterations = max_iterations
        self.history: list[dict[str, Any]] = []

    # -- public -------------------------------------------------------------
    def chat(self, message: str) -> str:
        self.history.append({"role": "user", "content": message})

        for iteration in range(1, self.max_iterations + 1):
            log.debug("iteration %d | history_len=%d", iteration, len(self.history))
            assistant_message = self._call_model()

            if not assistant_message.tool_calls:
                self.history.append(
                    {"role": "assistant", "content": assistant_message.content}
                )
                return assistant_message.content or ""

            # Record the assistant's tool-call request so the API can pair it
            # with the tool results we append next.
            self.history.append(assistant_message.model_dump(exclude_none=True))

            for tool_call in assistant_message.tool_calls:
                self.history.append(self._run_tool(tool_call))

        # Don't hide the failure behind a magic string; raise instead.
        raise RuntimeError(
            f"Agent did not produce a final answer after {self.max_iterations} iterations. "
            f"Last message role: {self.history[-1].get('role')}"
        )

    # -- internals ----------------------------------------------------------

    def _call_model(self):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": SYSTEM_PROMPT}, *self.history],
                tools=TOOLS,
                tool_choice="auto",
                parallel_tool_calls=False,  # deterministic, easier to trace
                temperature=0,             # deterministic tool selection
            )
        except APIError as e:
            # Surface API issues cleanly instead of crashing the loop mid-run.
            raise RuntimeError(f"OpenAI API error: {e}") from e
        return response.choices[0].message

    def _run_tool(self, tool_call) -> dict[str, Any]:
        name = tool_call.function.name
        log.info("tool call: %s", name)

        if name not in FUNCTIONS:
            payload = {"success": False, "error": f"Unknown tool: {name}"}
            return self._tool_message(tool_call, payload)

        try:
            args = json.loads(tool_call.function.arguments or "{}")
            log.info("  args: %s", args)
            result = FUNCTIONS[name](**args)
            payload = {"success": True, "result": result}
        except json.JSONDecodeError as e:
            payload = {"success": False, "error": f"Bad JSON arguments: {e}"}
        except TypeError as e:
            payload = {"success": False, "error": f"Bad arguments for {name}: {e}"}
        except Exception as e:  # noqa: BLE001 - tool errors must not kill the loop
            log.exception("Tool %s raised", name)
            payload = {"success": False, "error": str(e)}

        if not payload["success"]:
            log.warning("  tool failed: %s", payload.get("error"))
        else:
            log.info("  result: %s", payload["result"])

        return self._tool_message(tool_call, payload)

    @staticmethod
    def _tool_message(tool_call, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(payload),
        }

# ---------------------------------------------------------------------------
# Demo / tests
# ---------------------------------------------------------------------------

def main() -> None:
    # Each case gets a fresh agent so history can't leak between them.
    cases = [
        ("Process order ORD101", "expect discount applied, 1800 confirmed"),
        ("Process order ORD102", "expect NO discount, 500 confirmed"),
        ("Process order ORD103", "expect discount applied, 1350 confirmed"),
        ("Process order ORD999", "expect 'not found', no confirmation sent"),
    ]

    for message, expectation in cases:
        print("\n" + "=" * 72)
        print(f"USER: {message}")
        print(f"EXPECTATION: {expectation}")
        print("-" * 72)

        agent = OrderAgent()
        try:
            reply = agent.chat(message)
        except RuntimeError as e:
            reply = f"[agent error] {e}"
        print(f"ASSISTANT: {reply}")
        print(f"HISTORY: {len(agent.history)} messages")

if __name__ == "__main__":
    main()