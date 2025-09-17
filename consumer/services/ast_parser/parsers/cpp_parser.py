from typing import Dict, Any, List
from ..utils import traverse_tree
from tree_sitter import Parser, Language
from tree_sitter_cpp import language as get_cpp_language

class CPPParser:
    def __init__(self):
        self.parser = Parser()
        raw_lang = get_cpp_language()
        self.parser.language = Language(raw_lang)
        
    def extract_metadata(self, code: str) -> Dict[str, Any]:
        """Returns dict with keys: functions, variables, includes"""
        if not code.strip():
            return {}

        tree = self.parser.parse(bytes(code, "utf8"))

        functions = []
        variables = set()
        includes = []

        def visitor(node):
            # Function definitions (free functions or methods)
            if node.type in ["function_definition", "method_definition"]:
                func_info = self._extract_function_info(node)
                if func_info:
                    functions.append(func_info)

            # Variable declarations (local or global)
            elif node.type == "declaration":
                # Look for variable declarators
                for child in node.children:
                    if child.type == "init_declarator":
                        # Extract variable name (could be nested)
                        var_name = self._extract_variable_name(child)
                        if var_name:
                            variables.add(var_name)
                    elif child.type == "identifier":
                        # Simple declaration: int x;
                        variables.add(child.text.decode())

            # Preprocessor includes
            elif node.type == "preproc_include":
                includes.append(node.text.decode())

        traverse_tree(tree.root_node, visitor)

        return {
            "functions": functions,
            "variables": list(variables),
            "imports": includes  # Using "imports" key for compatibility (LLM expects it)
        }

    def _extract_function_info(self, node) -> Dict | None:
        """Extract function name, parameters, and line number."""
        # Function declarator is usually a child
        declarator = None
        for child in node.children:
            if child.type in ["function_declarator", "operator_function_declarator"]:
                declarator = child
                break

        if not declarator:
            return None

        # Extract function name
        func_name = None
        params = []

        for child in declarator.children:
            if child.type == "identifier":
                func_name = child.text.decode()
            elif child.type == "parameter_list":
                params = self._extract_parameters(child)

        if not func_name:
            return None

        return {
            "name": func_name,
            "params": params,
            "start_line": node.start_point[0] + 1
        }

    def _extract_parameters(self, param_list_node) -> List[str]:
        """Extract parameter names from parameter_list node."""
        params = []
        for child in param_list_node.children:
            if child.type == "parameter_declaration":
                # Find the identifier inside
                param_name = self._find_identifier_in_node(child)
                if param_name:
                    params.append(param_name)
            elif child.type == "identifier":  # Sometimes direct in list
                params.append(child.text.decode())
        return params

    def _find_identifier_in_node(self, node) -> str | None:
        """Recursively find first identifier in node."""
        if node.type == "identifier":
            return node.text.decode()
        for child in node.children:
            result = self._find_identifier_in_node(child)
            if result:
                return result
        return None

    def _extract_variable_name(self, init_declarator_node) -> str | None:
        """Extract variable name from init_declarator (e.g., int x = 5)."""
        # First child is usually the declarator (could be identifier or pointer, etc.)
        if init_declarator_node.child_count == 0:
            return None

        declarator = init_declarator_node.children[0]
        if declarator.type == "identifier":
            return declarator.text.decode()

        # Handle pointers: int *x = ...
        if declarator.type == "pointer_declarator" and declarator.child_count > 0:
            for child in declarator.children:
                if child.type == "identifier":
                    return child.text.decode()

        # Handle references: int &x = ...
        if declarator.type == "reference_declarator" and declarator.child_count > 0:
            for child in declarator.children:
                if child.type == "identifier":
                    return child.text.decode()

        return None