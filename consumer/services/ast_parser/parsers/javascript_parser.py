from typing import Dict, Any
from ..utils import traverse_tree
from tree_sitter import Parser, Language
from tree_sitter_javascript import language as get_js_language

class JavascriptParser:
    def __init__(self):
        self.parser = Parser()
        raw_lang = get_js_language()
        self.parser.language = Language(raw_lang) 
        
    def extract_metadata(self, code: str) -> Dict[str, Any]:
        if not code.strip():
            return {}

        tree = self.parser.parse(bytes(code, "utf8"))

        functions = []
        variables = set()
        imports = []

        def visitor(node):
            # Function declarations: function foo() {}
            if node.type == "function_declaration":
                if node.child_count > 1:
                    name_node = node.children[1]
                    if name_node.type == "identifier":
                        func_name = name_node.text.decode()
                        params = self._extract_params(node)
                        functions.append({
                            "name": func_name,
                            "params": params,
                            "start_line": node.start_point[0] + 1
                        })

            # Arrow functions assigned to variables: const foo = () => {}
            elif node.type == "variable_declarator":
                if node.child_count >= 2:
                    name_node = node.children[0]
                    value_node = node.children[1]
                    if name_node.type == "identifier" and value_node.type == "arrow_function":
                        func_name = name_node.text.decode()
                        params = self._extract_arrow_params(value_node)
                        functions.append({
                            "name": func_name,
                            "params": params,
                            "start_line": node.start_point[0] + 1
                        })

            # Variable declarations: let/const/var x = ...
            elif node.type == "variable_declarator":
                if node.child_count > 0 and node.children[0].type == "identifier":
                    var_name = node.children[0].text.decode()
                    variables.add(var_name)

            # Import statements
            elif node.type == "import_statement":
                imports.append(node.text.decode())

        traverse_tree(tree.root_node, visitor)

        return {
            "functions": functions,
            "variables": list(variables),
            "imports": imports
        }

    def _extract_params(self, func_node) -> list:
        if func_node.child_count < 3:
            return []
        # Params are usually at index 2 for function_declaration
        params_node = func_node.children[2]
        return self._collect_param_names(params_node)

    def _extract_arrow_params(self, arrow_node) -> list:
        if arrow_node.child_count == 0:
            return []
        # First child is parameters
        params_node = arrow_node.children[0]
        return self._collect_param_names(params_node)

    def _collect_param_names(self, params_node) -> list:
        params = []
        if params_node.type == "formal_parameters":
            for child in params_node.children:
                if child.type == "identifier":
                    params.append(child.text.decode())
                elif child.type == "assignment_pattern":
                    # Handle default params: (x = 1)
                    if child.child_count > 0 and child.children[0].type == "identifier":
                        params.append(child.children[0].text.decode())
        return params