# ast_parser/language_detector.py
"""
Detects primary language and sub-languages (e.g., JS inside HTML).
Used by parser.py to route to correct AST parser.
"""

import os
import re
from typing import Dict, List

def detect_language(filename: str, code: str) -> Dict[str, any]:
    """
    Returns dict: { "primary": str, "sub_languages": List[str] }
    Examples:
      - file.js → { "primary": "javascript", "sub_languages": [] }
      - file.html → { "primary": "html", "sub_languages": ["javascript", "css"] }
    """
    ext = os.path.splitext(filename)[1].lower()

    ext_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.html': 'html',
        '.htm': 'html',
        '.php': 'php',
        '.java': 'java',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.cs': 'csharp',
        '.c': 'c',
        '.cpp': 'cpp',    # ← Add these
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp',    # ← Treat .hpp as C++
    }

    primary = ext_map.get(ext, "unknown")

    # Detect sub-languages for multi-language files
    sub_languages = []

    if primary == "html":
        if re.search(r'<script[^>]*>', code, re.IGNORECASE):
            sub_languages.append("javascript")
        if re.search(r'<style[^>]*>', code, re.IGNORECASE):
            sub_languages.append("css")
        if "<?php" in code:
            sub_languages.append("php")

    elif primary == "php":
        if "<script" in code:
            sub_languages.append("javascript")

    return {
        "primary": primary,
        "sub_languages": sub_languages
    }