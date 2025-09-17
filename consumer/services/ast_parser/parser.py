# ast_parser/parser.py
"""
Main AST Parser Orchestrator.
One public function: parse_ast(code: str, filename: str) → str
Returns AST metadata as string to prepend to file content in diff.
"""

import logging
from typing import Optional, Dict, Any

from .language_detector import detect_language
from .parsers.python_parser import PythonParser
from .parsers.javascript_parser import JavascriptParser
from .parsers.html_parser import HTMLParser
from .parsers.php_parser import PHPParser
from .parsers.cpp_parser import CPPParser
from .parsers.universal_parser import UniversalParser

logger = logging.getLogger(__name__)


def parse_ast(code: str, filename: str) -> str:
    """
    Public entry point. Parses code and returns AST metadata string.
    Format: "[AST] Functions: f1, f2 | Variables: v1, v2 | Imports: i1, i2"
    Safe for all languages. Falls back to universal parser if needed.
    """
    try:
        # Detect primary language
        lang_info = detect_language(filename, code)
        primary_lang = lang_info.get("primary", "unknown")

        logger.debug(f"Detected language: {primary_lang} for {filename}")

        # Choose parser
        parser = _get_parser(primary_lang)

        # Parse and extract metadata
        metadata = parser.extract_metadata(code)

        # Format for LLM — minimal, clean, compatible
        parts = []

        if metadata.get("functions"):
            funcs = ", ".join(f["name"] for f in metadata["functions"][:10])  # cap at 10
            parts.append(f"Functions: {funcs}")

        if metadata.get("variables"):
            vars_ = ", ".join(metadata["variables"][:15])
            parts.append(f"Variables: {vars_}")

        if metadata.get("imports"):
            imports = ", ".join(metadata["imports"][:10])
            parts.append(f"Imports: {imports}")

        if not parts:
            return ""  # No AST metadata to add

        ast_line = "[AST] " + " | ".join(parts)
        return ast_line

    except Exception as e:
        logger.warning(f"AST parsing failed for {filename}: {e}")
        return ""  # Graceful degradation — never break the flow


def _get_parser(language: str):
    """Factory: returns parser instance based on language."""
    if language == "python":
        return PythonParser()
    elif language == "javascript":
        return JavascriptParser()
    elif language == "html":
        return HTMLParser()
    elif language == "php":
        return PHPParser()
    elif language == "cpp":  # ← ADD THIS
        return CPPParser()
    elif language == "c":    # ← Optional: reuse CPPParser for C files
        return CPPParser()
    else:
        return UniversalParser()
