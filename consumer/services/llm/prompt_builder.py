import json
from typing import List, Dict, Any

def build_prompt(
    files_data: List[Dict[str, Any]],
    issues: List[Dict] = None,
    include_raw_code: bool = True,
    model_role: str = "You are CodeEagle AI, an expert code reviewer..."
) -> str:
    """
    Build prompt for LLM using structured AST metadata.
    Optionally includes raw code for full context.

    Args:
        files_data: List of dicts with keys: "filename", "ast_metadata", "raw_code" (optional)
        issues: List of automated scan issues (from linters, etc.)
        include_raw_code: If False, sends only AST metadata (no raw code)
        model_role: System role description for LLM

    Returns:
        str: Fully formatted prompt ready for LLM
    """

    # Start with role and mission
    prompt_parts = [model_role, "\n## INPUT DATA\n"]

    # Build CODE CHANGES section
    code_changes = []
    for file_data in files_data:
        filename = file_data["filename"]
        ast_metadata = file_data.get("ast_metadata", "")
        raw_code = file_data.get("raw_code", "")

        section = f"File: {filename}\n"
        
        if ast_metadata:
            section += f"{ast_metadata}\n"
        
        if include_raw_code and raw_code:
            section += f"\n{raw_code}\n"
        elif not include_raw_code:
            section += "\n[Code content omitted — analysis based on AST metadata only]\n"

        code_changes.append(section.strip())

    prompt_parts.append("### CODE CHANGES:\n" + "\n\n".join(code_changes) + "\n")

    # Add automated scan results
    prompt_parts.append(f"\n### AUTOMATED SCAN RESULTS:\n{json.dumps(issues, indent=2) if issues else 'No automated issues detected'}\n")

    # Append analysis framework and output requirements (unchanged)
    prompt_parts.append(_get_analysis_framework())

    return "\n".join(prompt_parts)


def _get_analysis_framework() -> str:
    """
    Returns the fixed part of the prompt: analysis framework, output structure, examples.
    """
    return """
    ## ANALYSIS FRAMEWORK

    1. **SEVERITY LEVELS** (Use these exact terms):
    - `critical`: Security vulnerabilities, data loss risks, crashes, exploitable flaws
    - `high`: Major bugs, significant performance issues, memory leaks
    - `medium`: Code smells, maintainability issues, minor performance problems
    - `low`: Style issues, naming conventions, minor optimizations

    2. **ISSUE TYPES** (Use exact terms):
    - `security`: Vulnerabilities, injection risks, auth issues
    - `bug`: Logic errors, null pointers, race conditions
    - `performance`: Slow queries, memory leaks, inefficient algorithms
    - `best_practice`: Design patterns, SOLID violations, code structure
    - `style`: Formatting, naming, comments
    - `documentation`: Missing/incorrect docs

    3. **QUALITY SCORING**:
    - A+/A/A-: Production-ready, minimal issues
    - B+/B/B-: Good quality, minor improvements needed
    - C+/C/C-: Needs work, several issues to address
    - D/F: Major problems, not ready for merge

    ## OUTPUT REQUIREMENTS

    Return ONLY valid JSON matching this exact structure:

    {
    "summary": "Brief 4-5 sentences executive summary. Be specific about the main issues found.",
    "findings": [
        {
        "type": "security|bug|performance|best_practice|style|documentation",
        "severity": "critical|high|medium|low",
        "file": "exact/path/to/file.ext",
        "line": 42,
        "description": "Clear, specific explanation of the issue and its impact.",
        "suggestion": "Actionable fix with specific implementation details.",
        "vulnerable_code": "The exact problematic code (no markdown backticks)",
        "fixed_code": "The corrected code (no markdown backticks)"
        }
    ],
    "overall_score": "A+|A|A-|B+|B|B-|C+|C|C-|D|F"
    }

    ## REVIEW GUIDELINES

    1. **Be Specific**: Reference exact lines, variables, and functions
    2. **Be Actionable**: Every finding must have a clear fix
    3. **Be Accurate**: Don't invent issues that don't exist
    4. **Be Helpful**: Explain WHY something is a problem
    5. **Be Concise**: Get to the point without unnecessary words

    ## EXAMPLE OUTPUT

    {
        "summary": "Found 2 security vulnerabilities: SQL injection in auth module and XSS in user profile.",
        "findings": [
            {
            "type": "security",
            "severity": "critical",
            "file": "api/auth/login.py",
            "line": 45,
            "description": "SQL injection vulnerability. User input directly concatenated into query allows database manipulation.",
            "suggestion": "Use parameterized queries with placeholders to prevent injection.",
            "vulnerable_code": "query = f'SELECT * FROM users WHERE email = \\"email\\"'",
            "fixed_code": "query = 'SELECT * FROM users WHERE email = %s'\\ncursor.execute(query, (email,))"
            },
            {
            "type": "performance",
            "severity": "medium",
            "file": "api/data/processor.go",
            "line": 122,
            "description": "N+1 query problem in loop causes 100+ database calls for typical request.",
            "suggestion": "Batch fetch all required data before loop using JOIN or IN clause.",
            "vulnerable_code": "for _, id := range userIds {{\\n  user := db.GetUser(id)\\n}}",
            "fixed_code": "users := db.GetUsers(userIds) // Single query\\nfor _, user := range users {{"
            }
        ],
        "overall_score": "C+"
    }

    ## IMPORTANT RULES

    - Output ONLY valid JSON, no explanations or comments outside JSON
    - Use exact field names as specified
    - Don't include markdown backticks in code fields
    - Focus on real issues, not hypothetical problems
    - If no issues found, return empty findings array with score A or A+
    - Review ALL provided code thoroughly
    - For codes, make sure there is proper line breaks, spacing and indentation
    - Find as many issues as possible and maximum 5-8 per file ranking according to severity

    Now analyze the code and provide your review:
    """