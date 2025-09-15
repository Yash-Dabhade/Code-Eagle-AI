# services/comment_formatter.py

def format_review_comment(review: dict) -> str:
    """
    Format LLM review output into clean, professional GitHub Markdown comment.
    Inspired by CodeAnt AI and CodeRabbit style - minimal, clean, actionable.
    """
    findings = review.get("findings", [])
    summary = review.get("summary", "Code review completed.")
    overall_score = review.get("overall_score", "N/A")
    
    # Count findings by severity for summary
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for finding in findings:
        severity = finding.get("severity", "low").upper()
        if severity in severity_counts:
            severity_counts[severity] += 1
    
    # Start building comment
    comment_parts = []
    
    # Clean header with icon
    comment_parts.append("## 🤖 CodeEagle AI Review\n")
    
    # Executive summary in a clean box
    comment_parts.append("### 📊 Summary")
    comment_parts.append("```")
    comment_parts.append(f"Status: {get_status_text(overall_score)}")
    comment_parts.append(f"Risk Level: {get_risk_level(severity_counts)}")
    comment_parts.append(f"Files Analyzed: {len(set(f.get('file', '') for f in findings))}")
    comment_parts.append(f"Issues Found: {len(findings)}")
    if any(severity_counts.values()):
        issues_line = []
        if severity_counts["CRITICAL"]: issues_line.append(f"🔴 Critical: {severity_counts['CRITICAL']}")
        if severity_counts["HIGH"]: issues_line.append(f"🟠 High: {severity_counts['HIGH']}")
        if severity_counts["MEDIUM"]: issues_line.append(f"🟡 Medium: {severity_counts['MEDIUM']}")
        if severity_counts["LOW"]: issues_line.append(f"🔵 Low: {severity_counts['LOW']}")
        comment_parts.append(" | ".join(issues_line))
    comment_parts.append("```\n")
    
    # Main summary message
    if severity_counts["CRITICAL"] > 0:
        comment_parts.append(f"⚠️ **Action Required**: Found {severity_counts['CRITICAL']} critical issue(s) that must be addressed before merging.\n")
    elif severity_counts["HIGH"] > 0:
        comment_parts.append(f"⚠️ **Review Needed**: Found {severity_counts['HIGH']} high-priority issue(s) that should be addressed.\n")
    elif len(findings) > 0:
        comment_parts.append("✅ **Good to merge** after addressing minor suggestions.\n")
    else:
        comment_parts.append("✅ **Excellent!** No issues found. Code is ready to merge.\n")

    # Add findings if any
    if findings:
        comment_parts.append("### 🔍 Detailed Findings\n")
        
        # Group findings by file for better organization
        findings_by_file = {}
        for finding in findings:
            file_path = finding.get("file", "unknown")
            if file_path not in findings_by_file:
                findings_by_file[file_path] = []
            findings_by_file[file_path].append(finding)
        
        for file_path, file_findings in findings_by_file.items():
            # File header
            comment_parts.append(f"#### 📄 `{file_path}`\n")
            
            for finding in file_findings:
                severity = finding.get("severity", "unknown").upper()
                line_num = finding.get("line", "?")
                description = finding.get("description", "No description provided")
                suggestion = finding.get("suggestion", "No suggestion provided")
                vulnerable_code = finding.get("vulnerable_code", "")
                fixed_code = finding.get("fixed_code", "")
                finding_type = finding.get('type', 'unknown').replace('_', ' ').title()
                
                # Severity badge
                severity_badge = get_severity_badge(severity)
                
                # Clean finding box
                comment_parts.append(f"<details open>")
                comment_parts.append(f"<summary>{severity_badge} <strong>{finding_type}</strong> at line {line_num}</summary>\n")
                
                # Description
                comment_parts.append(f"**Issue**: {description}\n")
                
                # Suggestion
                comment_parts.append(f"**Recommendation**: {suggestion}\n")
                
                # Code diff if available
                if vulnerable_code or fixed_code:
                    # Auto-detect language
                    ext = file_path.split(".")[-1].lower() if "." in file_path else "txt"
                    lang = get_language_from_extension(ext)
                    
                    if vulnerable_code and fixed_code and vulnerable_code != fixed_code:
                        # Show diff style
                        comment_parts.append("```diff")
                        for line in vulnerable_code.split('\n'):
                            if line.strip():
                                comment_parts.append(f"- {line}")
                        for line in fixed_code.split('\n'):
                            if line.strip():
                                comment_parts.append(f"+ {line}")
                        comment_parts.append("```")
                    else:
                        # Show suggested fix only
                        comment_parts.append(f"**Suggested fix**:")
                        comment_parts.append(f"```{lang}")
                        comment_parts.append(fixed_code if fixed_code else vulnerable_code)
                        comment_parts.append("```")
                
                comment_parts.append("</details>\n")
        
        # Add helpful actions section
        comment_parts.append("---\n")
        comment_parts.append("### 💡 Next Steps\n")
        if severity_counts["CRITICAL"] > 0:
            comment_parts.append("1. **Fix critical issues** - These are blocking the merge")
        if severity_counts["HIGH"] > 0:
            comment_parts.append("2. **Address high-priority issues** - These could cause problems in production")
        if severity_counts["MEDIUM"] > 0:
            comment_parts.append("3. **Consider medium issues** - These improve code quality and maintainability")
        if severity_counts["LOW"] > 0:
            comment_parts.append("4. **Optional improvements** - Nice-to-have enhancements")
        comment_parts.append("")
    
    # Professional footer
    comment_parts.append("---")
    comment_parts.append("<sub>")
    comment_parts.append("🤖 **CodeEagle AI** | [Documentation](https://github.com/code-eagle) | [Report Issue](https://github.com/code-eagle/issues)")
    comment_parts.append("</sub>")
    
    return "\n".join(comment_parts)


def get_severity_badge(severity: str) -> str:
    """Return a styled badge for severity level."""
    badges = {
        "CRITICAL": "🔴 **CRITICAL**",
        "HIGH": "🟠 **HIGH**",
        "MEDIUM": "🟡 **MEDIUM**",
        "LOW": "🔵 **LOW**",
        "INFO": "ℹ️ **INFO**"
    }
    return badges.get(severity.upper(), "⚪ **UNKNOWN**")


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