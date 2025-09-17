from .helpers import get_language_from_extension, get_risk_level, get_severity_badge, get_status_text

def format_review_comment(review: dict) -> str:
    """
    Format LLM review output into clean, professional GitHub Markdown comment.
    Inspired by CodeAnt AI style - with proper tables, blocks, and spacing.
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
    
    # Header with professional styling
    comment_parts.append("# Code-Eagle AI Review\n")
    
    # Summary table
    comment_parts.append("## Summary")
    comment_parts.append("| Metric | Value |")
    comment_parts.append("|--------|-------|")
    comment_parts.append(f"| **Status** | {get_status_text(overall_score)} |")
    comment_parts.append(f"| **Risk Level** | {get_risk_level(severity_counts)} |")
    comment_parts.append(f"| **Files Analyzed** | {len(set(f.get('file', '') for f in findings))} |")
    comment_parts.append(f"| **Issues Found** | {len(findings)} |")
    

    # Main summary message with appropriate emoji
    comment_parts.append("\n## Overview")
    if severity_counts["CRITICAL"] > 0:
        comment_parts.append(f"⛔ Critical Issues Detected: {severity_counts['CRITICAL']} critical issue(s) must be addressed before merging.\n")
    elif severity_counts["HIGH"] > 0:
        comment_parts.append(f"⚠️ Review Needed: {severity_counts['HIGH']} high-priority issue(s) should be addressed.\n")
    elif len(findings) > 0:
        comment_parts.append("✅ Good to merge after addressing minor suggestions.\n")
    else:
        comment_parts.append("Excellent! No issues found. Code is ready to merge.\n")

    # Severity breakdown table
    if any(severity_counts.values()):
        comment_parts.append("\n## Issues by Severity")
        comment_parts.append("| Severity | Count |")
        comment_parts.append("|----------|-------|")
        for severity, count in severity_counts.items():
            if count > 0:
                comment_parts.append(f"| {get_severity_badge(severity)} | {count} |")
    
    # Add findings if any
    if findings:
        comment_parts.append("## Detailed Findings")
        
        # Group findings by file for better organization
        findings_by_file = {}
        for finding in findings:
            file_path = finding.get("file", "unknown")
            if file_path not in findings_by_file:
                findings_by_file[file_path] = []
            findings_by_file[file_path].append(finding)
        
        for file_path, file_findings in findings_by_file.items():
            # File header
            comment_parts.append(f"\n### `{file_path}`")
            
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
                
                # Finding header with collapsible section
                comment_parts.append(f"<details>")
                comment_parts.append(f"<summary>{severity_badge} {finding_type} at line {line_num}</summary>\n")
                
                # Description and suggestion in a clean box
                comment_parts.append("#### Description")
                comment_parts.append(f"{description}\n")
                
                comment_parts.append("#### Recommendation")
                comment_parts.append(f"{suggestion}\n")
                
                # Code diff if available
                if vulnerable_code or fixed_code:
                    # Auto-detect language
                    ext = file_path.split(".")[-1].lower() if "." in file_path else "txt"
                    lang = get_language_from_extension(ext)
                    
                    if vulnerable_code and fixed_code and vulnerable_code != fixed_code:
                        # Show diff style
                        comment_parts.append("#### Suggested Fix")
                        comment_parts.append("```diff")
                        comment_parts.append(f"# Before (line {line_num})")
                        for line in vulnerable_code.split('\n'):
                            if line.strip():
                                comment_parts.append(f"-{line}")
                        comment_parts.append(f"# After")
                        for line in fixed_code.split('\n'):
                            if line.strip():
                                comment_parts.append(f"+{line}")
                        comment_parts.append("```")
                    else:
                        # Show suggested fix only
                        comment_parts.append("#### Code Snippet")
                        comment_parts.append(f"```{lang}")
                        comment_parts.append(fixed_code if fixed_code else vulnerable_code)
                        comment_parts.append("```")
                
                comment_parts.append("</details>\n")
        
        # Add helpful actions section
        comment_parts.append("---")
        comment_parts.append("## Next Steps")
        steps = []
        if severity_counts["CRITICAL"] > 0:
            steps.append("1. **Fix critical issues** - These are blocking the merge")
        if severity_counts["HIGH"] > 0:
            steps.append("2. **Address high-priority issues** - These could cause problems in production")
        if severity_counts["MEDIUM"] > 0:
            steps.append("3. **Consider medium issues** - These improve code quality and maintainability")
        if severity_counts["LOW"] > 0:
            steps.append("4. **Optional improvements** - Nice-to-have enhancements")
        
        if steps:
            comment_parts.extend(steps)
        comment_parts.append("")
    
    # Professional footer
    comment_parts.append("---")
    comment_parts.append("*Generated by [CodeEagle AI](https://github.com/code-eagle) | [Documentation](https://github.com/code-eagle) | [Report Issue](https://github.com/code-eagle/issues)*")
    
    return "\n".join(comment_parts)

