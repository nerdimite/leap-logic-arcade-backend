import ast
import sys
import traceback
from io import StringIO
from typing import Any, Dict, Optional, Tuple


class CodeSandbox:
    """A simple sandbox for executing Python code with safety restrictions."""

    def __init__(
        self, max_execution_time: int = 10, allowed_modules: Optional[list] = None
    ):
        """Initialize the sandbox with execution time limits.

        Args:
            max_execution_time: Maximum execution time in seconds
            allowed_modules: List of module names that are allowed to be imported
        """
        self.max_execution_time = max_execution_time
        self.allowed_modules = allowed_modules or ["numpy", "scipy"]

        # Create a restricted globals dictionary with safe builtins
        restricted_builtins = {}
        safe_builtins = [
            "abs",
            "all",
            "any",
            "bool",
            "dict",
            "dir",
            "enumerate",
            "filter",
            "float",
            "format",
            "frozenset",
            "hash",
            "int",
            "isinstance",
            "issubclass",
            "len",
            "list",
            "map",
            "max",
            "min",
            "print",
            "range",
            "repr",
            "round",
            "set",
            "slice",
            "sorted",
            "str",
            "sum",
            "tuple",
            "type",
            "zip",
        ]

        for builtin in safe_builtins:
            if hasattr(__builtins__, builtin):
                restricted_builtins[builtin] = getattr(__builtins__, builtin)

        # Set up globals with restricted builtins
        self.globals = {"__builtins__": restricted_builtins}

        # Pre-import allowed modules
        for module_name in self.allowed_modules:
            try:
                # Use the built-in __import__ function directly
                module = __import__(module_name)
                self.globals[module_name] = module
            except ImportError:
                # Skip if module is not available
                pass

    def _is_safe_ast(self, code_ast: ast.AST) -> bool:
        """Check if the AST contains only safe operations.

        Args:
            code_ast: The AST to check

        Returns:
            True if the code is safe, False otherwise
        """
        # This is a simplified check - a real sandbox would be more comprehensive
        for node in ast.walk(code_ast):
            # Check imports against whitelist
            if isinstance(node, ast.Import):
                for name in node.names:
                    if name.name not in self.allowed_modules:
                        return False
            elif isinstance(node, ast.ImportFrom):
                if node.module not in self.allowed_modules:
                    return False
            # Prevent exec/eval
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in ["exec", "eval", "compile", "__import__"]:
                    return False
        return True

    def execute(self, code: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Execute code in the sandbox.

        Args:
            code: Python code to execute

        Returns:
            Tuple of (success, output, local_vars)
        """
        # Parse the code to check for unsafe operations
        try:
            code_ast = ast.parse(code)
            if not self._is_safe_ast(code_ast):
                return False, "Unsafe operations detected", {}
        except SyntaxError as e:
            return False, f"Syntax error: {str(e)}", {}

        # Capture stdout
        old_stdout = sys.stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        # Execute the code
        local_vars = {}
        success = True
        try:
            exec(code, self.globals, local_vars)
        except Exception as e:
            success = False
            print(f"Error: {str(e)}")
            print(traceback.format_exc())
        finally:
            sys.stdout = old_stdout

        return success, captured_output.getvalue(), local_vars


async def davinci_coder(
    code: str,
) -> str:
    """Execute a code snippet and return the output in a stateless sandbox.

    This is a stateless code execution sandbox that only persists for the duration of the execution.
    Beyond the basic Python libraries, it has access to the following preloaded modules:
    - math: Available without importing
    - numpy: Available without importing
    - scipy: Available without importing

    You don't need to import these libraries in your code as they are already preloaded.
    There's a limit of 10 seconds for the execution of the code.
    You might wanna use print statements to view the output of the code.

    Args:
        code: The Python code snippet to execute.

    Returns:
        The output of the code execution as a string.
    """
    sandbox = CodeSandbox(allowed_modules=["math", "numpy", "scipy"])
    success, output, variables = sandbox.execute(code)

    print(f"Execution successful: {success}")
    print(f"Output:\n{output}")
    print(f"Variables: {variables}")

    return {
        "success": success,
        "output": output,
        "variables": variables,
    }
