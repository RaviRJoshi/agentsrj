# %%
from openai import OpenAI
from dotenv import load_dotenv
import json

MODEL="gpt-5.5"

system_prompt = f"""
You are a small little useful Geographer who can also do some basic 
arithmetic stuff or adding an email to a file etc. 
I'll be asking you questions about a place, and you will answer 
them based on the information you have. If you don't know the answer,
 say so. Never make up an answer.  If you know the answer, answer 
 it in a few paragraphs.
"""

history = []
load_dotenv(override=True)
openai = OpenAI()


def record_email_tool(email):
	print(f"Tool called to record an email: {email}")
	with open("emails.txt", "a", encoding="utf-8") as f:
		f.write(email + "\n")
	return "Email Received"

def process_numbers_tool(a: int, b: int) -> int:
    total = a + b
    if total > 100:
        return a * b
    return total

def calculate_discount_tool(amount: int) -> int:
    return amount * 0.1 if amount > 1000 else 0

def process_order_tool(amount: int) -> int:
    return amount - calculate_discount_tool(amount)


record_email_tool_json = {
  "type": "function",
  "function": {	
      "name": "record_email_tool",
      "description": "Use this tool to record that a user provided their address",
      "parameters": {
        "type": "object",
        "properties": {
          "email": { "type": "string", "description": "The email address of this user"}
        },
        "required": ["email"],
        "additionalProperties": False
      }
  }
}

process_numbers_tool_json = {
     "type": "function",
     "function": {
        "name": "process_numbers_tool",
        "description": "Add two numbers. If more than 100, multiply them",
        "parameters": {
          "type": "object",
          "properties": {
            "a": { "type": "number" },
            "b": { "type": "number" }
          },
          "required": [  "a", "b" ],
          "additionalProperties": False
        },
        "strict": True
        }
  }

process_order_tool_json = {
  "type": "function",
  "function": {
    "name": "process_order_tool",
    "description": "",
    "parameters": {
      "type": "object",
      "properties": {
        "amount": {
          "type": "integer"
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

calculate_discount_tool_json = {
  "type": "function",
  "function": {
    "name": "calculate_discount_tool",
    "description": "",
    "parameters": {
      "type": "object",
      "properties": {
        "amount": {
          "type": "integer"
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

TOOLS = [record_email_tool_json, 
         process_numbers_tool_json,
         process_order_tool_json,
         calculate_discount_tool_json]

available_functions = {
    "process_numbers_tool": process_numbers_tool,
    "record_email_tool": record_email_tool,
    "process_order_tool": process_order_tool,
    "calculate_discount_tool": calculate_discount_tool
}


# %%
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



# %%
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

         

# %%
def Test(message):
    history.clear()
    response = chat(message)
    print (response)  

#  %%
if __name__ == "__main__":

    # message = "Please process an order of 1500 dollars."
    # Test(message)
    # print("-----------------------")
    # print(history)
    # print("-----------------------")

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
                             