import requests
import jwt
import time
from config.env import env
from utils.logger import setup_logger
from typing import List, Dict, Any, Optional
import base64

logger = setup_logger(__name__)

class GitHubService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(GitHubService, cls).__new__(cls)
        return cls._instance

    def __init__(self, token: str = None, app_token: str = None):
        # Avoid re-initializing if already done
        if hasattr(self, '_initialized') and self._initialized:
            return

        self.token = token or None
        self.app_token = app_token
        self.base_url = "https://api.github.com"
        self._installation_token = None
        self._token_expires_at = 0

        # Load app credentials from .env if available
        self.app_id = env.GITHUB_APP_ID
        self.app_private_key_base64 = env.GITHUB_APP_PRIVATE_KEY_BASE64
        self.installation_id = env.GITHUB_APP_INSTALLATION_ID

        self._initialized = True

    def _get_app_jwt(self) -> str:
        """Generate a JWT for GitHub App authentication"""
        if not self.app_id or not self.app_private_key_base64:
            raise ValueError("GITHUB_APP_ID or GITHUB_APP_PRIVATE_KEY_BASE64 not set in env")

        # Decode private key from Base64
        private_key_bytes = base64.b64decode(self.app_private_key_base64)
        private_key = private_key_bytes.decode('utf-8')

        payload = {
            "iat": int(time.time()) - 60,  # Issued 1 min ago to account for clock skew
            "exp": int(time.time()) + (10 * 60),  # Expires in 10 minutes
            "iss": self.app_id
        }

        return jwt.encode(payload, private_key, algorithm="RS256")

    def _get_installation_token(self) -> str:
        """Get an installation access token (cached until expiry)"""
        now = time.time()
        if self._installation_token and self._token_expires_at > now + 60:
            return self._installation_token

        jwt_token = self._get_app_jwt()
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CodeEagle-AI"
        }

        if not self.installation_id:
            raise ValueError("GITHUB_APP_INSTALLATION_ID not set in env")

        url = f"{self.base_url}/app/installations/{self.installation_id}/access_tokens"
        response = requests.post(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        self._installation_token = data["token"]
        self._token_expires_at = now + 3600  # Assume 1 hour expiry (GitHub default)

        logger.info("New GitHub App installation token generated.")
        return self._installation_token

    def _get_headers(self) -> Dict[str, str]:
        """Get appropriate headers for GitHub API requests"""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CodeEagle-AI"
        }

        if self.app_token:
            headers["Authorization"] = f"Bearer {self.app_token}"
        elif self.app_id and self.app_private_key_base64 and self.installation_id:
            # Use GitHub App installation token
            token = self._get_installation_token()
            headers["Authorization"] = f"Bearer {token}"
        elif self.token:
            # Fallback to Personal Access Token
            headers["Authorization"] = f"token {self.token}"
        else:
            logger.warning("No authentication token available for GitHub API")

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
            logger.error(f"Error fetching PR files: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
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
            logger.error(f"Error fetching PR details: {e}")
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
            logger.error(f"Error fetching file content: {e}")
            return ""

    def post_review_comments(self, repo: str, pr_number: int, review_data: dict) -> bool:
        """
        Post structured, beautifully formatted review comments to GitHub PR — like CodeAntAI
        Uses Pull Request Reviews API with inline comments.
        Falls back to simple comment if API fails.
        """
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}/reviews"
        headers = self._get_headers()
        headers["Content-Type"] = "application/json"

        # Format findings as GitHub PR review comments
        comments = []
        findings = review_data.get("findings", [])
        
        for finding in findings:
            # You may need to map 'line' to actual 'position' in diff later
            # For now, position=1 is a placeholder — GitHub requires position relative to PR diff
            comments.append({
                "path": finding.get("file", ""),
                "position": finding.get("line", 1),  # ⚠️ In production, map to actual diff hunk position
                "body": (
                    f"### 🔍 **{finding.get('severity', 'info').upper()}**: {finding.get('type', '').replace('_', ' ').title()}\n"
                    f"```diff\n{finding.get('code_snippet', '')}\n```\n"
                    f"**Description**: {finding.get('description', 'No description provided')}\n\n"
                    f"**Suggestion**: {finding.get('suggestion', 'No suggestion provided')}\n"
                    f">  *Reported by CodeEagle AI*"
                )
            })

        # Main review body with summary, score, and emoji flair
        data = {
            "body": (
                f"## 🦅 **CodeEagle AI Automated Review**\n\n"
                f"**Summary**: {review_data.get('summary', 'Review completed successfully')}\n"
                f"**Overall Score**: `{review_data.get('overall_score', 'N/A')}/10`\n"
                f"**Total Issues Found**: `{len(comments)}`\n\n"
                f"---\n"
                f"*Powered by AI. Review suggestions critically.*"
            ),
            "event": "COMMENT",  # Doesn't approve/reject — just comments
            "comments": comments
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                logger.info("✅ GitHub PR review posted successfully with inline comments.")
                return True
            else:
                logger.warning(f"⚠️ GitHub PR review API returned {response.status_code}: {response.text}")
                # FALLBACK: Post simple summary comment if review API fails
                fallback_comment = (
                    f"## 🦅 CodeEagle AI Review (Fallback)\n\n"
                    f"*Unable to post inline comments.*\n"
                    f"**Summary**: {review_data.get('summary', 'Review completed')}\n"
                    f"**Score**: `{review_data.get('overall_score', 'N/A')}/10`\n"
                    f"**Issues**: `{len(comments)}`\n\n"
                    f"Please check logs or try re-running analysis."
                )
                return self.post_simple_comment(repo, pr_number, fallback_comment)

        except Exception as e:
            logger.error(f"GitHub API error posting review: {e}")
            # Fallback to simple comment
            fallback_comment = (
                f"## CodeEagle AI Review (Error)\n\n"
                f"*Failed to post detailed review due to error: `{str(e)}`*\n"
                f"**Summary**: {review_data.get('summary', 'Review failed')}\n"
                f"Please check service logs for details."
            )
            return self.post_simple_comment(repo, pr_number, fallback_comment)


    def post_simple_comment(self, repo: str, pr_number: int, comment: str) -> bool:
        """
        Post a simple Markdown comment on PR (as issue comment)
        Used as fallback or for general messages.
        """
        url = f"{self.base_url}/repos/{repo}/issues/{pr_number}/comments"
        headers = self._get_headers()
        headers["Content-Type"] = "application/json"

        data = {"body": comment}

        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 201:
                logger.info("Simple comment posted successfully.")
                return True
            else:
                logger.error(f"Failed to post simple comment: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Exception posting simple comment: {e}")
            return False


# Singleton instance export
github_service = GitHubService()