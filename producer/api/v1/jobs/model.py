# Define all pydantic models here

from typing import Dict, Any
from pydantic import BaseModel
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Job(BaseModel):
    repo: str
    pr_number: int
    head_sha: str
    status: JobStatus = JobStatus.PENDING

def create_job_payload(repo: str, pr_number: int, head_sha: str, status: JobStatus = JobStatus.PENDING.value) -> Dict[str, Any]:
    # Validate and create job payload
    job = Job(
        repo=repo,
        pr_number=pr_number,
        head_sha=head_sha,
        status=status
    )
    
    return job.model_dump()
    