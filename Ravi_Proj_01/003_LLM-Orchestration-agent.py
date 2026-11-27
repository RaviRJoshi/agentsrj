# %%
from openai import OpenAI
from dotenv import load_dotenv
import json

MODEL="gpt-5.5"

system_prompt = """
You are an order processing assistant.

You have access to the following tools:

1. get_order_details_tool:
   Retrieves order details using an order ID.

2. calculate_discount_tool:
   Calculates a 10% discount on an amount if the amount equals or exceeds 1000.

3. send_order_confirmation_tool:
   Sends an order confirmation for the given order ID and final amount.

Your workflow:

1. First retrieve the order details.
2. Examine the returned order amount.
3. If the amount equals or exceeds 1000, call calculate_discount_tool.
4. If the amount is 1000 or less, do not call calculate_discount_tool.
5. Calculate the final amount.
6. Send the order confirmation using send_order_confirmation_tool with the order ID and final amount.
7. Present the order details, discount and final amount.

Important:
- Always retrieve order details before calculating a discount.
- Never invent order amounts.
- If an order is not found, report that fact.
- Do not call calculate_discount_tool when it is not required.
"""

history = []
load_dotenv(override=True)
openai = OpenAI()

def send_order_confirmation_tool(order_id: str, final_amount: float) -> str:
    print(f"Tool called to send order confirmation for order {order_id} with final amount {final_amount}")
    # Simulate sending an email or notification
    return f"Order confirmation sent for order {order_id} with final amount {final_amount}"


def get_order_details_tool(order_id: str) -> dict:

    # Simulated database
    orders = {
        "ORD101": 2000,
        "ORD102": 500,
        "ORD103": 1500,
        "ORD104": 1000
    }

    if order_id not in orders:
        return {"error": "Order not found"}

    return {
        "order_id": order_id,
        "amount": orders[order_id]
    }

def calculate_discount_tool(amount: float) -> float:
    return amount * 0.10 if amount >= 1000.0 else 0.0

get_order_details_tool_json = {
  "type": "function",
  "function": {
    "name": "get_order_details_tool",
    "description": "Retrieve details of an order based on the provided order ID.",
    "parameters": {
      "type": "object",
      "properties": {
        "order_id": {
          "type": "string"
        }
      },
      "required": [ "order_id" ],
      "additionalProperties": False
    },
    "strict": True
  }
}

calculate_discount_tool_json = {
  "type": "function",
  "function": {
    "name": "calculate_discount_tool",
    "description": "Calculate discount on an order",
    "parameters": {
      "type": "object",
      "properties": {
        "amount": {
          "type": "number"
        }
      },
      "required": [ "amount" ],
      "additionalProperties": False
    },
    "strict": True
  }
}

send_order_confirmation_tool_json = {
  "type": "function",
  "function": {
    "name": "send_order_confirmation_tool",
    "description": "Send an order confirmation for the given order ID and final amount.",
    "parameters": {
      "type": "object",
      "properties": {
        "order_id": {
          "type": "string"
        },
        "final_amount": {
          "type": "number"
        }
      },
      "required": [
        "order_id",
        "final_amount"
      ],
      "additionalProperties": False
    },
    "strict": True
  }
}

TOOLS = [get_order_details_tool_json,
         calculate_discount_tool_json,
         send_order_confirmation_tool_json]

available_functions = {
    "get_order_details_tool": get_order_details_tool,
    "calculate_discount_tool": calculate_discount_tool,
    'send_order_confirmation_tool': send_order_confirmation_tool
}


# %%  execute_tool
def execute_tool(tool_call):

    # Extract function name
    function_name = tool_call.function.name
    print(f"\nExecuting tool: {function_name}")

    # Extract JSON arguments
    arguments     = json.loads( tool_call.function.arguments )
    print(f"Arguments: {arguments}")

    # Check whether function exists
    if function_name not in available_functions:
        raise ValueError(f"Unknown tool: {function_name}")

    # Get actual Python function
    function_to_call = available_functions[function_name]

    # Execute function using unpacked arguments
    result = function_to_call(**arguments)

    print(f"Tool result: {result}")

    return result





# %% chat
def chat(message):
    history.clear()
    history.append({"role": "user", "content": message})

    max_iterations = 10
    for _ in range(max_iterations):
        messagesToAssistant = [{"role": "system", "content": system_prompt}] + history
        responseFromAssistant = openai.chat.completions.create(
            model=MODEL,
            messages=messagesToAssistant,
            tools=TOOLS,
            parallel_tool_calls=False
        )
        assistant_message = responseFromAssistant.choices[0].message

        if assistant_message.tool_calls:
            print("Tool Execution Needed")
            # Record the assistant's tool-call request in history
            history.append(assistant_message.model_dump(exclude_none=True))

            # Execute every requested tool and append each result linked by tool_call_id
            for tool_call in assistant_message.tool_calls:
                try:
                    result = execute_tool(tool_call)
                    tool_output = json.dumps({"success": True, "result": result})
                except Exception as e:
                    tool_output = json.dumps({"success": False, "error": str(e)})

                history.append({ "role": "tool", 
                    "tool_call_id": tool_call.id,
                    "content": tool_output
                })
        else:
            history.append({"role": "assistant", "content": assistant_message.content})
            return assistant_message.content

    return "Maximum tool execution iterations reached."



# _______________________________________________________
#  %%
if __name__ == "__main__":
  # print("-----------------------")
  message = "Process order ORD104"
  print(chat(message))
  # print("-----------------------")
