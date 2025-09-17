from tree_sitter import Parser
from typing import Dict, Any
from ..utils import traverse_tree
from tree_sitter import Parser, Language
from tree_sitter_python import language as get_python_language

class PythonParser:
    def __init__(self):
        self.parser = Parser()
        raw_lang = get_python_language()  
        self.parser.language = Language(raw_lang)

    def extract_metadata(self, code: str) -> Dict[str, Any]:
        if not code.strip():
            return {}

        tree = self.parser.parse(bytes(code, "utf8"))

        functions = []
        variables = set()
        imports = []

        def visitor(node):
            if node.type == "function_definition":
                if len(node.children) > 1:
                    name_node = node.children[1]
                    func_name = name_node.text.decode()
                    params = self._extract_params(node)
                    functions.append({
                        "name": func_name,
                        "params": params,
                        "start_line": node.start_point[0] + 1
                    })

            elif node.type == "assignment":
                if node.child_count > 0 and node.children[0].type == "identifier":
                    var_name = node.children[0].text.decode()
                    variables.add(var_name)

            elif node.type in ["import_statement", "import_from_statement"]:
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
        params_node = func_node.children[2]
        params = []
        for child in params_node.children:
            if child.type == "identifier":
                params.append(child.text.decode())
        return params