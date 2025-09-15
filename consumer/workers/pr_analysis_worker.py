# from services.llm_service import analyze_code
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
    for file in pr_files:
        file_path = file.get("filename")
        file_content = github_service.get_file_content(job.repo, file_path, job.head_sha)
        logger.info(f"Fetched content for {file_path} ({len(file_content)} chars)\n\n")


    # # Fetch code diff
    # diff = fetch_pr_diff(job.repo, job.pr_number, job.head_sha)
    # print(f"📄 Fetched diff ({len(diff)} chars)")
    
    # # Build AST analysis
    # ast_analysis = build_ast(diff)
    # print(f"🌳 AST analysis completed: {len(ast_analysis.get('functions', []))} functions found")
    
    # # Get automated scan issues (placeholder)
    # issues = ["Potential SQL injection detected", "Hardcoded secret found"]
    
    # # Analyze with LLM using AST context
    # review = analyze_code(diff, ast_analysis, issues)
    # print(f"🧠 LLM analysis completed: {len(review.get('findings', []))} findings")
    
    review= {
        "summary": "This is a placeholder review summary.",
        "findings": [
            {
                "type": "issue",
                "description": "This is a placeholder issue description.",
                "line": 42
            }
        ],
        "suggestions": [
            {
                "description": "This is a placeholder suggestion.",
                "line": 56
            }
        ]
    }

    # Post structured review comments to GitHub
    success = github_service.create_review_comment(job.repo, job.pr_number, review)
    
    if success:
        logger.info("Review posted successfully")
    else:
        logger.error("Failed to post review")