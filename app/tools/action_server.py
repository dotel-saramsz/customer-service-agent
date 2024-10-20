from tools.definitions import tools_func_mapping
import json


def execute_tool_function(
    function_name: str, function_arguments: str | None = None
) -> str:
    """Calls a function and returns the result."""
    callable_function = tools_func_mapping.get(function_name)

    if not callable_function:
        tool_response = {"error": "Requested tool is not found."}
    else:
        # Convert the function arguments from a string to a dict
        function_arguments_dict = (
            json.loads(function_arguments) if function_arguments else {}
        )

        print("---------------------")
        print(
            f"Calling tool ({function_name}) with arguments {function_arguments_dict}"
        )
        # Call the function and return the result
        tool_response = callable_function(**function_arguments_dict)

    print(f"Tool response: {tool_response}")
    print("---------------------")

    return json.dumps(tool_response)
