import re
from typing import Dict, Any, List
from .javascript_parser import JavascriptParser
from tree_sitter import Parser, Language
from tree_sitter_html import language as get_html_language

class HTMLParser:
    def __init__(self):
        self.parser = Parser()
        raw_lang = get_html_language()
        self.parser.language = Language(raw_lang)
        self.js_parser = JavascriptParser()
        
    def extract_metadata(self, code: str) -> Dict[str, Any]:
        metadata = {
            "functions": [],
            "variables": [],
            "imports": []
        }

        # Extract <script> blocks (JavaScript only)
        script_blocks = self._extract_script_blocks(code)
        for block in script_blocks:
            try:
                js_meta = self.js_parser.extract_metadata(block)
                metadata["functions"].extend(js_meta.get("functions", []))
                metadata["variables"].extend(js_meta.get("variables", []))
                metadata["imports"].extend(js_meta.get("imports", []))
            except Exception:
                continue  # Skip if JS parsing fails

        # Deduplicate variables
        metadata["variables"] = list(set(metadata["variables"]))

        return metadata

    def _extract_script_blocks(self, html: str) -> List[str]:
        """Extracts content between <script> tags (ignores src=, only inline)."""
        # Match <script>...</script> but not <script src=...>
        pattern = r'<script(?!\s*src\s*=)[^>]*>(.*?)</script>'
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
        return [m.strip() for m in matches if m.strip()]