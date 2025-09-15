from services.llm_review_service import analyze_code
from models.pr_job import PRJobData
from services.github_service import github_service
from utils.logger import setup_logger

logger = setup_logger(__name__)

def process_job(job_data: dict):
    # Extract job data
    job = PRJobData.from_dict(job_data)
    logger.info(f"🔧 Processing job: {job.repo} PR #{job.pr_number}")

    # Fetch changed files
    pr_files = github_service.get_pr_files(job.repo, job.pr_number)
    logger.info(f"Fetched {len(pr_files)} changed files\n\n")

    # Fetch file contents
    diff=""
    for file in pr_files:
        file_path = file.get("filename")
        diff+=file_path+"\n\n"
        file_content = github_service.get_file_content(job.repo, file_path, job.head_sha)
        diff+=file_content
        logger.info(f"Fetched content for {file_path} ({len(file_content)} chars)\n\n")


    # # Build AST analysis
    # ast_analysis = build_ast(diff)
    # logger.info(f"🌳 AST analysis completed: {len(ast_analysis.get('functions', []))} functions found")
    
    # # Analyze with LLM using AST context
    review = analyze_code(diff, "")
    logger.info(f"🧠 LLM analysis completed: {len(review.get('findings', []))} findings")
    
       # 🚧 TEMP: Since we don't have real diff positions, post as simple top-level comment
    # Format a nice Markdown summary from the LLM review
    findings = review.get("findings", [])
    summary = review.get("summary", "Code review completed.")
    overall_score = review.get("overall_score", "N/A")

    comment_body = f"""
## 🦅 CodeEagle AI Review

✅ **Summary**: {summary}  
📊 **Overall Score**: `{overall_score}`  
🔎 **Findings**: `{len(findings)}` issues detected

---

"""

    if findings:
        for idx, finding in enumerate(findings, 1):
            comment_body += f"""
            ### Finding #{idx}: **{finding.get('severity', 'unknown').upper()}** — {finding.get('type', '').replace('_', ' ').title()}

            **File**: `{finding.get('file', 'unknown')}`  
            **Line**: `{finding.get('line', '?')}`

            **Description**:  
            > {finding.get('description', 'No description provided')}

            **Suggestion**:  
            {finding.get('suggestion', 'No suggestion provided')}

            ---
            """
    else:
        comment_body += "No issues found. Great job! 👏"

    comment_body += "\n> *Powered by CodeEagle AI — improving code, one PR at a time.*"

    # Post as simple comment — no diff position needed
    success = github_service.post_simple_comment(job.repo, job.pr_number, comment_body)

    if success:
        logger.info("Review comment posted successfully as top-level comment.")
    else:
        logger.error("Failed to post review comment.")