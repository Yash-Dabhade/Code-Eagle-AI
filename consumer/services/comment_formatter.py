# services/comment_formatter.py

def format_review_comment(review: dict) -> str:
    """
    Format LLM review output into clean, professional GitHub Markdown comment.
    Clean, minimal design similar to CodeAnt AI.
    """
    findings = review.get("findings", [])
    summary = review.get("summary", "Code review completed.")
    overall_score = review.get("overall_score", "N/A")

    # Start building comment - NO INDENTATION for proper GitHub rendering
    comment_parts = []
    
    # Header
    comment_parts.append("## 🤖 CodeEagle AI Review\n")
    
    # Summary section with clean formatting
    comment_parts.append(f"{summary}\n")
    comment_parts.append("")
    comment_parts.append(f"**Overall Score**: `{overall_score}`")
    comment_parts.append(f"**Findings**: `{len(findings)}` issues detected\n")
    comment_parts.append("---\n")

    if findings:
        for idx, finding in enumerate(findings, 1):
            # Extract fields with fallbacks
            severity = finding.get("severity", "unknown").upper()
            file_path = finding.get("file", "unknown")
            line_num = finding.get("line", "?")
            description = finding.get("description", "No description provided")
            suggestion = finding.get("suggestion", "No suggestion provided")
            vulnerable_code = finding.get("vulnerable_code", "# No code shown")
            fixed_code = finding.get("fixed_code", "# No fix shown")
            finding_type = finding.get('type', 'unknown').replace('_', ' ').title()

            # Auto-detect language from file extension
            ext = file_path.split(".")[-1].lower() if "." in file_path else "txt"
            lang_map = {
                "js": "javascript", "ts": "typescript", "jsx": "jsx", "tsx": "tsx",
                "py": "python", "go": "go", "java": "java", "kt": "kotlin", "rs": "rust",
                "rb": "ruby", "php": "php", "cs": "csharp", "swift": "swift", "m": "objectivec",
                "c": "c", "cpp": "cpp", "h": "c", "hpp": "cpp", "sh": "bash", "sql": "sql",
                "html": "html", "css": "css", "json": "json", "yaml": "yaml", "yml": "yaml",
                "toml": "toml", "md": "markdown", "xml": "xml", "tsx": "typescript"
            }
            lang = lang_map.get(ext, "plaintext")

            # Severity emoji mapping
            severity_emoji = {
                "CRITICAL": "🔴",
                "HIGH": "🟠", 
                "MEDIUM": "🟡",
                "LOW": "🔵",
                "INFO": "⚪"
            }
            emoji = severity_emoji.get(severity, "⚪")

            # Build finding section
            comment_parts.append(f"### {emoji} Finding #{idx}: {severity} - {finding_type}\n")
            comment_parts.append(f"**File**: `{file_path}`")
            comment_parts.append(f"**Line**: `{line_num}`\n")
            comment_parts.append(f"> {description}\n")
            comment_parts.append(f"💡 **Suggestion**:")
            comment_parts.append(f"{suggestion}\n")
            
            # Code comparison block
            comment_parts.append("```" + lang)
            comment_parts.append("# ❌ Vulnerable")
            comment_parts.append(vulnerable_code)
            comment_parts.append("")
            comment_parts.append("# ✅ Fixed")
            comment_parts.append(fixed_code)
            comment_parts.append("```\n")
            
            # Add separator between findings (except last one)
            if idx < len(findings):
                comment_parts.append("---\n")
    else:
        comment_parts.append("✅ **No issues found. Great job!**\n")

    # Footer
    comment_parts.append("---")
    comment_parts.append("*Powered by CodeEagle AI — improving code, one PR at a time.*")
    
    # Join all parts with newlines
    return "\n".join(comment_parts)