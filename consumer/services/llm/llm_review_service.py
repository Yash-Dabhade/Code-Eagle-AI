# services/llm_review_service.py

import ollama
from config.env import env
import json
from .prompt_builder import build_prompt
from services.github.github_service import github_service
from utils.logger import setup_logger
from services.ast_parser.parser import parse_ast

logger = setup_logger(__name__)

def analyze_code(job: dict, pr_files: list, issues: list) -> dict:
    """
    Analyze code changes and return structured, professional feedback.
    """

    try:
        data=[]
        for file in pr_files:
            try:
                file_path = file.get("filename", "unknown")
                file_content = github_service.get_file_content(job.repo, file_path, job.head_sha)
                
                ast_metadata = parse_ast(file_content, file_path)

                data.append({"filename": file_path, "raw_code": file_content, "ast_metadata": ast_metadata})
                logger.info(f"Fetched content for {file_path} ({len(file_content)} chars)\n")

            except Exception as e:
                logger.error(f"Failed to fetch content for {file_path}: {e}")
                data.append({"filename": file_path, "raw_code": "[ERROR: Failed to load file content]", "ast_metadata": {}})

        prompt = build_prompt(files_data=data, issues=issues, include_raw_code=True)
        
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
            logger.error(f"LLM Raw Response:\n{json.dumps(result, indent=2)}\n")
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