
import inspect
import typing
import json

# ___________________
def process_numbers(a: int, b: int) -> int:
    total = a + b
    if total > 100:
        return a * b
    return total

def record_email_tool(email):
	print(f"Tool called to record an email: {email}")
	with open("emails.txt", "a", encoding="utf-8") as f:
		f.write(email + "\n")
	return "Email Received"



def python_type_to_json_type(annotation):
    mapping = {
        int: "integer",
        float: "number",
        str: "string",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null"
    }

    return mapping.get(annotation, "string")


def function_to_tool(func):
    signature = inspect.signature(func)
    hints = typing.get_type_hints(func)

    properties = {}
    required = []

    for name, param in signature.parameters.items():
        annotation = hints.get(name, str)

        properties[name] = {
            "type": python_type_to_json_type(annotation)
        }

        if param.default == inspect.Parameter.empty:
            required.append(name)

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": inspect.getdoc(func) or "",
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False
            },
            "strict": True
        }
    }

if __name__ == "__main__":
    tool_schema = function_to_tool(process_numbers)
    print(json.dumps(tool_schema, indent=2))

    tool_schema = function_to_tool (record_email_tool)
    print(json.dumps(tool_schema, indent=2))