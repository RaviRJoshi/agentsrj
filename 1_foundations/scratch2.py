# %%
from openai import OpenAI
from dotenv import load_dotenv
import json

# %%
MODEL="gpt-5.5"

system_prompt = """
    You are a helpful assistant.

    You have access to two tools:

    1. process_numbers_tool:
       Processes two integers and returns a result.

    2. record_email_tool:
       Records an email address.

    Use the appropriate tool whenever the user's
    request requires it.

    After receiving tool results, explain the
    result to the user in natural language.

    For other questions, answer only if you know the answer. If you don't
    know say so. DO NOT MAKE UP AN ANSWER.
    """
history = []
load_dotenv(override=True)
openai = OpenAI()



# %%

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
