from services.llm.llm_review_service import analyze_code
from models.pr_job import PRJobData
from services.github.github_service import github_service
from utils.logger import setup_logger

logger = setup_logger(__name__)

def process_job(job_data: dict):
    """
    Process a PR analysis job: fetch files, send to LLM, post review comment.
    """
    try:
        # Extract job data
        job = PRJobData.from_dict(job_data)
        logger.info(f"Processing job: {job.repo} PR #{job.pr_number}")

        # Fetch changed files
        pr_files = github_service.get_pr_files(job.repo, job.pr_number)
        if not pr_files:
            logger.warning("No files found in PR.")
            return

        logger.info(f"Fetched {len(pr_files)} changed files\n")

        issues = []

        # Generate analysis
        logger.info("Starting LLM analysis...")
        logger.info(f"Files to analyze: {[f['filename'] for f in pr_files]}")
        review = analyze_code(job, pr_files, issues)
        logger.info(f"LLM analysis completed: {len(review.get('findings', []))} findings")
        logger.info(f"Review Summary: {review.get('summary', '')}\n")
        if not review or "findings" not in review:
            logger.error("Invalid review format received from LLM.")
            return
        
        # Format and post to github
        review_success = github_service.post_detailed_review(job.repo, job.pr_number, review)
        if review_success:
            logger.info("Review comment posted successfully as top-level comment.")
        else:
            logger.error("Failed to post review comment.")
   
    except Exception as e:
        logger.error(e)