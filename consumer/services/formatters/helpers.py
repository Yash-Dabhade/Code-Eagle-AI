# Keep the helper functions the same as before
def get_severity_badge(severity: str) -> str:
    """Return a styled badge for severity level."""
    badges = {
        "CRITICAL": "🔴 CRITICAL",
        "HIGH": "🟠 HIGH",
        "MEDIUM": "🟡 MEDIUM",
        "LOW": "🔵 LOW",
        "INFO": "ℹ️ INFO"
    }
    return badges.get(severity.upper(), "⚪ UNKNOWN")

def get_status_text(score: str) -> str:
    """Convert letter grade to status text."""
    if score in ["A+", "A", "A-"]:
        return "✅ Excellent - Ready to merge"
    elif score in ["B+", "B", "B-"]:
        return "⚠️ Good - Minor issues to address"
    elif score in ["C+", "C", "C-"]:
        return "⚠️ Needs Improvement"
    elif score in ["D", "F"]:
        return "❌ Critical Issues Found"
    return "🔍 Review Complete"

def get_risk_level(severity_counts: dict) -> str:
    """Determine overall risk level from severity counts."""
    if severity_counts["CRITICAL"] > 0:
        return "🔴 Critical"
    elif severity_counts["HIGH"] > 0:
        return "🟠 High"
    elif severity_counts["MEDIUM"] > 0:
        return "🟡 Medium"
    elif severity_counts["LOW"] > 0:
        return "🔵 Low"
    return "✅ None"

def get_language_from_extension(ext: str) -> str:
    """Map file extension to language for syntax highlighting."""
    lang_map = {
        "js": "javascript", "ts": "typescript", "jsx": "jsx", "tsx": "tsx",
        "py": "python", "go": "go", "java": "java", "kt": "kotlin", "rs": "rust",
        "rb": "ruby", "php": "php", "cs": "csharp", "swift": "swift",
        "c": "c", "cpp": "cpp", "h": "c", "hpp": "cpp", "sh": "bash",
        "sql": "sql", "html": "html", "css": "css", "scss": "scss",
        "json": "json", "yaml": "yaml", "yml": "yaml", "xml": "xml",
        "toml": "toml", "md": "markdown", "dockerfile": "dockerfile",
        "makefile": "makefile", "cmake": "cmake"
    }
    
    return lang_map.get(ext.lower(), "plaintext")