# services/llm_review_service.py

import ollama
from config.env import env
import json

def analyze_code(diff: str, issues: list) -> dict:
    """
    Analyze code changes and return structured, professional feedback.
    Follows CodeAnt AI and CodeRabbit best practices for actionable reviews.
    """

    prompt = f"""
        You are CodeEagle AI, an expert code reviewer with deep expertise in security, performance, and best practices. 
        Provide actionable, specific feedback that helps developers improve their code.

        ## YOUR MISSION
        Review the provided code changes and identify real, impactful issues. Focus on problems that matter:
        - Security vulnerabilities that could be exploited
        - Bugs that will cause runtime errors or incorrect behavior  
        - Performance issues that impact user experience
        - Code that violates established best practices
        - Style and documentation improvements that enhance maintainability
        - Quality scoring to reflect readiness for production

        ## INPUT DATA

        ### CODE CHANGES:
        {diff}

        ### AUTOMATED SCAN RESULTS:
        {issues if issues else "No automated issues detected"}

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

        {{
        "summary": "Brief 4-5 sentences executive summary. Be specific about the main issues found.",
        "findings": [
            {{
            "type": "security|bug|performance|best_practice|style|documentation",
            "severity": "critical|high|medium|low",
            "file": "exact/path/to/file.ext",
            "line": 42,
            "description": "Clear, specific explanation of the issue and its impact.",
            "suggestion": "Actionable fix with specific implementation details.",
            "vulnerable_code": "The exact problematic code (no markdown backticks)",
            "fixed_code": "The corrected code (no markdown backticks)"
            }}
        ],
        "overall_score": "A+|A|A-|B+|B|B-|C+|C|C-|D|F"
        }}

        ## REVIEW GUIDELINES

        1. **Be Specific**: Reference exact lines, variables, and functions
        2. **Be Actionable**: Every finding must have a clear fix
        3. **Be Accurate**: Don't invent issues that don't exist
        4. **Be Helpful**: Explain WHY something is a problem
        5. **Be Concise**: Get to the point without unnecessary words

        ## EXAMPLE OUTPUT

        {{
            "summary": "Found 2 security vulnerabilities: SQL injection in auth module and XSS in user profile.",
            "findings": [
                {{
                "type": "security",
                "severity": "critical",
                "file": "api/auth/login.py",
                "line": 45,
                "description": "SQL injection vulnerability. User input directly concatenated into query allows database manipulation.",
                "suggestion": "Use parameterized queries with placeholders to prevent injection.",
                "vulnerable_code": "query = f'SELECT * FROM users WHERE email = \\"email\\"'",
                "fixed_code": "query = 'SELECT * FROM users WHERE email = %s'\\ncursor.execute(query, (email,))"
                }},
                {{
                "type": "performance",
                "severity": "medium",
                "file": "api/data/processor.go",
                "line": 122,
                "description": "N+1 query problem in loop causes 100+ database calls for typical request.",
                "suggestion": "Batch fetch all required data before loop using JOIN or IN clause.",
                "vulnerable_code": "for _, id := range userIds {{\\n  user := db.GetUser(id)\\n}}",
                "fixed_code": "users := db.GetUsers(userIds) // Single query\\nfor _, user := range users {{"
                }}
            ],
            "overall_score": "C+"
        }}

        ## IMPORTANT RULES

        - Output ONLY valid JSON, no explanations or comments outside JSON
        - Use exact field names as specified
        - Don't include markdown backticks in code fields
        - Focus on real issues, not hypothetical problems
        - If no issues found, return empty findings array with score A or A+
        - Review ALL provided code thoroughly
        - For codes, make sure there is proper line breaks, spacing and indentation

        Now analyze the code and provide your review:
        """

    try:
        response = ollama.generate(
            model=env.OLLAMA_MODEL,
            prompt=prompt,
            format="json",
            options={
                "temperature": 0.6,  # Lower temperature for more consistent output
                "top_p": 0.9,
                "num_ctx": 16384,    # Increased context for larger diffs
                "num_predict": 4096  # Allow longer responses
            }
        )

        try:
            result = json.loads(response["response"])
            
            # Validate and clean the response
            result = validate_and_clean_review(result)
            return result

        except (json.JSONDecodeError, ValueError) as e:
            return fallback_review(f"JSON parsing error: {str(e)}")

    except Exception as e:
        return fallback_review(f"Analysis error: {str(e)}")


def validate_and_clean_review(review: dict) -> dict:
    """
    Validate and clean the LLM-generated review to ensure it conforms to the expected schema.
    Ensures all required fields are present, types are correct, and values are valid.

    Args:
        review (dict): Raw review output from the LLM (parsed from JSON)

    Returns:
        dict: Cleaned and validated review with guaranteed structure
    """
    # Ensure top-level fields exist
    review.setdefault("summary", "Code review completed.")
    review.setdefault("findings", [])
    review.setdefault("overall_score", "B")

    # Validate and clean findings
    cleaned_findings = []
    valid_severities = ["critical", "high", "medium", "low"]
    valid_types = [
        "security", 
        "bug", 
        "performance", 
        "best_practice", 
        "style", 
        "documentation"
    ]

    for finding in review.get("findings", []):
        if not isinstance(finding, dict):
            continue  # Skip non-dict findings

        cleaned_finding = {
            "type": finding.get("type", "best_practice"),
            "severity": finding.get("severity", "medium"),
            "file": str(finding.get("file", "unknown")),
            "line": int(finding.get("line", 0)) if str(finding.get("line", "")).isdigit() else 0,
            "description": str(finding.get("description", "Issue detected")).strip(),
            "suggestion": str(finding.get("suggestion", "Review this code section")).strip(),
            "vulnerable_code": str(finding.get("vulnerable_code", "")).strip(),
            "fixed_code": str(finding.get("fixed_code", "")).strip()
        }

        # Normalize and validate severity
        if cleaned_finding["severity"].lower() not in valid_severities:
            cleaned_finding["severity"] = "medium"
        else:
            cleaned_finding["severity"] = cleaned_finding["severity"].lower()

        # Normalize and validate type
        if cleaned_finding["type"].lower() not in valid_types:
            cleaned_finding["type"] = "best_practice"
        else:
            cleaned_finding["type"] = cleaned_finding["type"].lower()

        cleaned_findings.append(cleaned_finding)

    review["findings"] = cleaned_findings

    # Validate overall score
    valid_scores = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"]
    if review["overall_score"] not in valid_scores:
        review["overall_score"] = "B"

    return review

def fallback_review(error_message: str) -> dict:
    """
    Generate a safe fallback review when code analysis fails.
    Ensures the output still conforms to the expected JSON structure,
    preventing breaking changes due to errors in LLM processing.

    Args:
        error_message (str): Description of the error encountered

    Returns:
        dict: Fallback review with error summary and minimal valid structure
    """
    return {
        "summary": f"Automated review could not be completed due to an internal error: {error_message}",
        "findings": [],
        "overall_score": "F"
    }