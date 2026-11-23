# %%
from openai import OpenAI
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
from IPython.display import Markdown, display
import gradio as gr
import json

# %%
load_dotenv(override=True)
openai = OpenAI()

# %%
reader = PdfReader("twin/linkedin.pdf")
linkedin = ""
for page in reader.pages:
    text = page.extract_text()
    if text:
        linkedin += text

#print(linkedin)


# %%
with open("twin/summary.txt", "r", encoding="utf-8") as f:
    summary = f.read()

# %%
system_prompt = f"""
You are a small little useful Geographer who can also do some basic stuff like arithmetic or adding an email to a file etc. I'll be asking you questions about a place, and you will answer them based on the information 
you have. If you don't know the answer, say so. Never make up an answer. If you know the answer, answer it in a few paragraphs.
"""

# %%
messages = [
    {"role": "system", "content": system_prompt}
 #   ,     {"role": "user", "content": "Tell me about bangalore, Karnataka?"}
]      

# %%
def record_email_tool(email):
	print(f"Tool called to record an email: {email}")
	with open("emails.txt", "a", encoding="utf-8") as f:
		f.write(email + "\n")
	return "Email Received"

# %%
#record_email_tool("ravi@duck.com")

# %%
record_email_tool_json = {
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

# %%
tools = [{"type": "function", "function": record_email_tool_json}]

# %%
tools

# %%
def chat(message, history):
	messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": message}]
	response = openai.chat.completions.create(model="gpt-5.4", messages=messages, tools=tools)
		 
	if response.choices[0].finish_reason=="tool_calls":
			message = response.choices[0].message
			tool_call = message.tool_calls[0]
			email = json.loads(tool_call.function.arguments).get("email")
			record_email_tool(email)
			messages.append(message)
			messages.append({"role": "tool", "content": "Email recorded", "tool_call_id": tool_call.id})
			response = openai.chat.completions.create(model="gpt-5.4", messages=messages, tools=tools)
			
	return response.choices[0].message.content

# %%
gr.ChatInterface(chat).launch(inbrowser=True)


