
import inspect
import typing
import json


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


def add_number_tool(num1, num2):
    return num1 + num2



if __name__ == "__main__":
    tool_schema = function_to_tool(add_number_tool)
    print(json.dumps(tool_schema, indent=2))

