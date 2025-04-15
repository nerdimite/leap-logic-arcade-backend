from typing import Optional

import openai
from pydantic import BaseModel


def generate_function_schema(model: BaseModel, name: Optional[str] = None):
    """Generate a function definition based on a Pydantic model.

    This function converts a Pydantic model into a function schema that can be used
    with OpenAI's function calling API. It wraps the model in a function definition
    with the specified name.

    Args:
        model: A Pydantic model class that defines the structure and validation rules
              for the function parameters.
        name: A string representing the name of the function in the schema. If not provided, the name will be the title of the model or the name of the model class.

    Returns:
        dict: A dictionary containing the function schema with "type": "function" added,
              compatible with OpenAI's function/tool calling interface.
    """
    if name is None:
        if model.model_config.get("title"):
            name = model.model_config["title"]
        else:
            name = model.__name__

    _schema = openai.pydantic_function_tool(model, name=name)
    return {"type": "function", **_schema["function"]}
