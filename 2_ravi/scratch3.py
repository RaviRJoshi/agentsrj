
import json
from openai import OpenAI

# --------------------------------------------------
# 1. OpenAI Client
# --------------------------------------------------

client = OpenAI()  # Reads OPENAI_API_KEY from environment

MODEL = "gpt-5.4"


# --------------------------------------------------
# 2. Define Python Functions (Tools)
# --------------------------------------------------

def process_numbers(a: int, b: int) -> int:
    total = a + b

    if total > 100:
        return a * b

    return total


def record_email_tool(email: str) -> str:
    # Replace this with your actual email recording logic
    print(f"Recording email: {email}")

    return f"Email {email} recorded successfully."


# --------------------------------------------------
# 3. Define Tool JSON Schemas
# --------------------------------------------------

process_numbers_json = {
    "type": "function",
    "function": {
        "name": "process_numbers",
        "description": "Process two integers and return the result.",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "integer",
                    "description": "First number"
                },
                "b": {
                    "type": "integer",
                    "description": "Second number"
                }
            },
            "required": ["a", "b"],
            "additionalProperties": False
        },
        "strict": True
    }
}


record_email_tool_json = {
    "type": "function",
    "function": {
        "name": "record_email_tool",
        "description": "Record an email address.",
        "parameters": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "Email address to record"
                }
            },
            "required": ["email"],
            "additionalProperties": False
        },
        "strict": True
    }
}


# Collection of tools passed to the LLM
tools = [
    process_numbers_json,
    record_email_tool_json
]


# --------------------------------------------------
# 4. Function Registry
# --------------------------------------------------

# Maps LLM function names to actual Python functions

available_functions = {
    "process_numbers": process_numbers,
    "record_email_tool": record_email_tool
}


# --------------------------------------------------
# 5. Execute Tool Requested by LLM
# --------------------------------------------------

def execute_tool(tool_call):

    function_name = tool_call.function.name

    # Extract JSON arguments
    arguments = json.loads(tool_call.function.arguments)

    print(f"\nExecuting tool: {function_name}")
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


# --------------------------------------------------
# 6. Main Agent Function
# --------------------------------------------------

def chat_with_llm(user_message):

    system_prompt = """
    You are a helpful assistant.

    You have access to two tools:

    1. process_numbers:
       Processes two integers and returns a result.

    2. record_email_tool:
       Records an email address.

    Use the appropriate tool whenever the user's
    request requires it.

    After receiving tool results, explain the
    result to the user in natural language.
    """

    # Initial conversation
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_message
        }
    ]

    # --------------------------------------------------
    # Agent Loop
    # --------------------------------------------------

    max_iterations = 10

    for iteration in range(max_iterations):

        print(f"\nLLM Call: {iteration + 1}")

        # Call LLM
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools
        )

        assistant_message = response.choices[0].message

        # ----------------------------------------------
        # Case 1: No tool calls - final answer
        # ----------------------------------------------

        if not assistant_message.tool_calls:

            print("\nFinal LLM Response:")
            return assistant_message.content

        # ----------------------------------------------
        # Case 2: LLM requested tool execution
        # ----------------------------------------------

        print("\nLLM requested tool execution")

        # Append assistant's tool-call message
        messages.append(
            assistant_message.model_dump(exclude_none=True)
        )

        # Execute all requested tools
        for tool_call in assistant_message.tool_calls:

            try:
                result = execute_tool(tool_call)

                tool_content = json.dumps({
                    "success": True,
                    "result": result
                })

            except Exception as e:

                print(f"Tool execution error: {e}")

                tool_content = json.dumps({
                    "success": False,
                    "error": str(e)
                })

            # ------------------------------------------
            # Send tool result back to LLM
            # ------------------------------------------

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_content
            })

    return "Maximum tool execution iterations reached."


# --------------------------------------------------
# 7. Main Program
# --------------------------------------------------

if __name__ == "__main__":

    print("Simple LLM Agent")
    print("----------------")

    while True:

        user_input = input("\nYou: ")

        if user_input.lower() in ["exit", "quit"]:
            break

        answer = chat_with_llm(user_input)

        print(f"\nAssistant: {answer}")

    print("\nAgent terminated.")
