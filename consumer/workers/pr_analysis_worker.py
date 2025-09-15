from services.llm_review_service import analyze_code
from models.pr_job import PRJobData
from services.github_service import github_service
from services.comment_formatter import format_review_comment
from utils.logger import setup_logger

logger = setup_logger(__name__)

def process_job(job_data: dict):
    """
    Process a PR analysis job: fetch files, send to LLM, post review comment.
    """
    try:
        # Extract job data
        job = PRJobData.from_dict(job_data)
        logger.info(f"🔧 Processing job: {job.repo} PR #{job.pr_number}")

        # Fetch changed files
        pr_files = github_service.get_pr_files(job.repo, job.pr_number)
        if not pr_files:
            logger.warning("No files found in PR.")
            return

        logger.info(f"Fetched {len(pr_files)} changed files\n")

        # Build pseudo-diff for LLM (full content of each file)
        diff = ""
        for file in pr_files:
            file_path = file.get("filename", "unknown")
            diff += f"File: {file_path}\n\n"
            
            try:
                file_content = github_service.get_file_content(job.repo, file_path, job.head_sha)
                diff += file_content + "\n\n"
                logger.info(f"Fetched content for {file_path} ({len(file_content)} chars)\n")
            except Exception as e:
                logger.error(f"Failed to fetch content for {file_path}: {e}")
                diff += "[ERROR: Failed to load file content]\n\n"

        # TEMP: Simulate automated scan findings (empty for now — you can populate later)
        issues = []  # ← You can populate this from linters, scanners, etc.

        # Analyze with LLM — pass diff + issues
        review = analyze_code(diff, issues)
        logger.info(f"🧠 LLM analysis completed: {len(review.get('findings', []))} findings")

        # Post to GitHub
        success = github_service.post_review_comments(job.repo, job.pr_number, review)

        if success:
            logger.info("Review comment posted successfully as top-level comment.")
        else:
            logger.error("Failed to post review comment.")
   
    except Exception as e:
        logger.error(e)