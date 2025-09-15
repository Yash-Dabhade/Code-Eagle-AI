import requests
from config.env import env
from utils.logger import setup_logger
from typing import List, Dict, Any

logger = setup_logger(__name__)

class GitHubService:
    def __init__(self, token: str = None, app_token: str = None):
        self.token = token or env.GITHUB_TOKEN
        self.app_token = app_token
        self.base_url = "https://api.github.com"
        
    def _get_headers(self) -> Dict[str, str]:
        """Get appropriate headers for GitHub API requests"""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CodeEagle-AI"
        }
        
        if self.app_token:
            headers["Authorization"] = f"Bearer {self.app_token}"
        elif self.token:
            headers["Authorization"] = f"token {self.token}"
            
        return headers
    
    def get_pr_files(self, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """
        Get all files changed in a pull request
        API: GET /repos/{owner}/{repo}/pulls/{pull_number}/files
        """
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}/files"
        headers = self._get_headers()
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching PR files: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            return []
    
    def get_pr_details(self, repo: str, pr_number: int) -> Dict[str, Any]:
        """
        Get pull request details
        API: GET /repos/{owner}/{repo}/pulls/{pull_number}
        """
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}"
        headers = self._get_headers()
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching PR details: {e}")
            return {}
    
    def get_file_content(self, repo: str, file_path: str, ref: str) -> str:
        """
        Get file content from a specific ref (branch/commit)
        API: GET /repos/{owner}/{repo}/contents/{path}
        """
        url = f"{self.base_url}/repos/{repo}/contents/{file_path}"
        headers = self._get_headers()
        params = {"ref": ref}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            content_data = response.json()
            
            # Decode base64 content
            import base64
            content = base64.b64decode(content_data["content"]).decode("utf-8")
            return content
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching file content: {e}")
            return ""
    
    def create_review_comment(self, repo: str, pr_number: int, review_data: dict) -> bool:
        """
        Create a review comment on a pull request
        API: POST /repos/{owner}/{repo}/pulls/{pull_number}/reviews
        """
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}/reviews"
        headers = self._get_headers()
        
        try:
            response = requests.post(url, headers=headers, json=review_data)
            response.raise_for_status()
            return True
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating review comment: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            return False

github_service = GitHubService()
