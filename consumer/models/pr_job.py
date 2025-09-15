from typing import Dict, Any

class PRJobData:
    def __init__(self, repo: str, pr_number: int, head_sha: str, status: str = "pending"):
        self.repo = repo
        self.pr_number = pr_number
        self.head_sha = head_sha
        self.status = status

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            repo=data["repo"],
            pr_number=data["pr_number"],
            head_sha=data["head_sha"]
        )