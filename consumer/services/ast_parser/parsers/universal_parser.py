import re
from typing import Dict, List, Any

class UniversalParser:
    def extract_metadata(self, code: str) -> Dict[str, Any]:
        functions = []
        variables = set()
        imports = []

        lines = code.splitlines()

        # Heuristic: function-like patterns
        func_patterns = [
            r'^\s*def\s+([a-zA-Z_]\w*)',           # Python
            r'^\s*function\s+([a-zA-Z_]\w*)',      # JS
            r'^\s*const\s+([a-zA-Z_]\w*)\s*=\s*function\b',  # JS const fn
            r'^\s*let\s+([a-zA-Z_]\w*)\s*=\s*function\b',    # JS let fn
            r'^\s*func\s+([a-zA-Z_]\w*)',          # Go
            r'^\s*public\s+function\s+([a-zA-Z_]\w*)', # PHP
            r'^\s*private\s+function\s+([a-zA-Z_]\w*)',
            r'^\s*protected\s+function\s+([a-zA-Z_]\w*)',
        ]

        for line in lines:
            for pattern in func_patterns:
                match = re.search(pattern, line)
                if match:
                    functions.append({"name": match.group(1), "params": []})
                    break

        # Heuristic: assignment patterns
        assign_pattern = r'^\s*([a-zA-Z_]\w*)\s*[+\-*/]?=\s*[^=]'
        for line in lines:
            match = re.search(assign_pattern, line)
            if match:
                variables.add(match.group(1))

        # Heuristic: import/require/include
        import_keywords = ['import', 'require', 'include', 'using', 'from', 'require_once']
        for line in lines:
            line_stripped = line.strip()
            if any(line_stripped.startswith(kw) for kw in import_keywords):
                imports.append(line_stripped)

        return {
            "functions": functions[:5],
            "variables": list(variables)[:10],
            "imports": imports[:5]
        }