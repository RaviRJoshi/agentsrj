# %%
from openai import OpenAI
from dotenv import load_dotenv
from openai import OpenAI
import json

load_dotenv(override=True)
openai = OpenAI()


system_prompt = f"""
You are a small little useful Geographer who can also do some basic 
stuff like arithmetic or adding an email to a file etc. 
I'll be asking you questions about a place, and you will answer 
them based on the information you have. If you don't know the answer,
 say so. Never make up an answer.  If you know the answer, answer 
 it in a few paragraphs.
"""

history = []

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

tools = [record_email_tool_json, process_numbers_tool_json]

available_functions = {
    "process_numbers_tool": process_numbers_tool,
    "record_email_tool": record_email_tool
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
def chat(message, history):

    messagesToLlm = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": message}]
    responseFromLlm = openai.chat.completions.create(model="gpt-5.4", messages = messagesToLlm, tools=tools)
    assistant_message = responseFromLlm.choices[0].message

    
    if assistant_message.tool_calls:
        print( "Tool Execution Needed")
        for tool_call in assistant_message.tool_calls:
            return execute_tool(tool_call)

    return assistant_message.content

         

# %%
def Test():
    message1 = "insert email address duck@example.com"
    message2 = "Process numbers 64 and 54."

    response = chat(message1, history)
    print (response)
    response = chat(message2, history)
    print (response)


#  %%
if __name__ == "__main__":
    Test()



    #  while True:
    #     user_input = input("\nYou> ")
    #     if user_input.lower() in ("exit", "quit"): 
    #          break
    #     else:
    #         answer = chat(user_input, history = history)
    #         print(answer)        
                             