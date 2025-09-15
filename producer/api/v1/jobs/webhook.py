# Webhook to listen the PR events and enqueue jobs

from fastapi import APIRouter, Request, HTTPException, status
from services.rabbitmq_service import enqueue_job
from .model import create_job_payload, JobStatus
from .helpers import verify_signature
import json
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


@router.post("/webhook")
async def github_webhook(request: Request):
    """Handle GitHub webhook events."""

    payload = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    
    logger.info(f"Received webhook from {request.client}")

    if not verify_signature(payload, signature):
        logger.error("Invalid signature - rejecting webhook")
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        event = json.loads(payload.decode())

        if event.get("action") in ["opened", "synchronize"]:
            # Deal with pull request events
            pr = event["pull_request"]
            
            logger.info(f"Processing PR #{pr['number']} in repo {pr['base']['repo']['full_name']}")

            job = create_job_payload(
                repo=pr["base"]["repo"]["full_name"],
                pr_number=pr["number"],
                head_sha=pr["head"]["sha"],
                status=JobStatus.PENDING.value
            )
            
            enqueue_job(job)

            logger.info(f"Job enqueued for PR #{pr['number']}")
            return {"status": "Job enqueued"}
        
        else:
            logger.info(f"Ignored action: {event.get('action')}")
            return {"status": "Ignored"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")