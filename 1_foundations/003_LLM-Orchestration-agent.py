# %%
from openai import OpenAI
from dotenv import load_dotenv
import json

MODEL="gpt-5.5"

system_prompt = f"""
You are a small little useful assistant  

You have access to a few tools that can help you do your job.
You can call these tools when you need to perform specific tasks.
The tools you have access to are:
1. get_order_details_tool(order_id: str) -> dict
   - This tool retrieves the details of an order based on the provided order ID.
2. calculate_discount_tool(amount: float) -> float
   - This tool calculates a discount based on the provided amount.
3. process_order_tool(amount: float) -> float
   - This tool processes an order based on the provided amount.
When you need to use a tool, you will call it with the appropriate parameters.

"""

history = []
load_dotenv(override=True)
openai = OpenAI()

def get_order_details_tool(order_id: str) -> dict:

    # Simulated database
    orders = {
        "ORD101": 2000,
        "ORD102": 500,
        "ORD103": 1500
    }

    if order_id not in orders:
        return {"error": "Order not found"}

    return {
        "order_id": order_id,
        "amount": orders[order_id]
    }

def calculate_discount_tool(amount: float) -> float:
    return amount * 0.10 if amount > 1000 else 0.0

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
      "required": [
        "order_id"
      ],
      "additionalProperties": False
    },
    "strict": True
  }
}

calculate_discount_tool_json = {
  "type": "function",
  "function": {
    "name": "calculate_discount_tool",
    "description": "IF the amount is greater than 1000, calculate a 10% discount, otherwise return 0",
    "parameters": {
      "type": "object",
      "properties": {
        "amount": {
          "type": "number"
        }
      },
      "required": [
        "amount"
      ],
      "additionalProperties": False
    },
    "strict": True
  }
}

TOOLS = [get_order_details_tool_json,
         calculate_discount_tool_json]

available_functions = {
    "get_order_details_tool": get_order_details_tool,
    "calculate_discount_tool": calculate_discount_tool
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
    history.append({"role": "user", "content": message})

    max_iterations = 10
    for _ in range(max_iterations):
        messagesToAssistant = [{"role": "system", "content": system_prompt}] + history
        responseFromAssistant = openai.chat.completions.create(
            model=MODEL,
            messages=messagesToAssistant,
            tools=TOOLS,
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

         



# %% Test
def Test(message):
    history.clear()
    response = chat(message)
    print (response)  



# _______________________________________________________
#  %%
if __name__ == "__main__":


    message = "Process email duck@example.com"
    Test(message)
    print("-----------------------")
    print(history)
    print("-----------------------")



    #  while True:
    #     user_input = input("\nYou> ")
    #     if user_input.lower() in ("exit", "quit"): 
    #          break
    #     else:
    #         answer = chat(user_input, history = history)
    #         print(answer)        
                             