from config.env import env
import hashlib
import hmac
from utils.logger import setup_logger

logger = setup_logger(__name__)

def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify GitHub webhook signature."""
    if not signature:
        logger.error("No signature provided")
        return False
    
    try:
        expected = hmac.new(
            env.GITHUB_WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected, signature.split("=")[1])
    
    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return False
