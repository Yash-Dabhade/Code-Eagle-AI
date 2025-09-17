from typing import Dict, Any
from ..utils import traverse_tree
from tree_sitter import Parser, Language
from tree_sitter_php import language_php as get_php_language

class PHPParser:
    def __init__(self):
        self.parser = Parser()
        raw_lang = get_php_language()
        self.parser.language = Language(raw_lang)

    def extract_metadata(self, code: str) -> Dict[str, Any]:
        if not code.strip():
            return {}

        # Prepend <?php if missing (tree-sitter-php requires it)
        if not code.strip().startswith('<?php'):
            code = '<?php\n' + code

        tree = self.parser.parse(bytes(code, "utf8"))

        functions = []
        variables = set()
        imports = []

        def visitor(node):
            # Function declarations
            if node.type == "function_definition":
                if node.child_count > 1:
                    name_node = node.children[1]
                    if name_node.type == "name":
                        func_name = name_node.text.decode()
                        params = self._extract_params(node)
                        functions.append({
                            "name": func_name,
                            "params": params,
                            "start_line": node.start_point[0] + 1
                        })

            # Variable assignments: $x = ...
            elif node.type == "assignment_expression":
                left = node.children[0] if node.child_count > 0 else None
                if left and left.type == "variable_name":
                    var_name = left.text.decode()
                    variables.add(var_name)

            # Use statements (imports)
            elif node.type == "use_declaration":
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
        params_node = func_node.children[2]  # formal_parameters
        params = []
        for child in params_node.children:
            if child.type == "parameter_declaration":
                for sub in child.children:
                    if sub.type == "variable_name":
                        params.append(sub.text.decode())
                        break
        return params