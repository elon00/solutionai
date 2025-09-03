from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from .database import get_db
from .config import settings
import logging

logger = logging.getLogger(__name__)


def get_current_api_key(request: Request, db: Session = Depends(get_db)) -> str:
    """
    Extract and validate API key from request headers
    """
    api_key = request.headers.get("X-Api-Key")

    if not api_key:
        logger.warning("Missing API key in request")
        raise HTTPException(
            status_code=401,
            detail="API key required. Please provide X-Api-Key header."
        )

    # Check if API key is in allowed list
    if api_key not in settings.allowed_api_keys:
        logger.warning(f"Invalid API key attempted: {api_key[:8]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    # TODO: Add database check for API key validity
    # This would check if the key exists in the database and is active

    return api_key


def validate_admin_key(request: Request) -> bool:
    """
    Validate admin API key for admin endpoints
    """
    admin_key = request.headers.get("X-Admin-Key")
    expected_admin_key = settings.secret_key

    if not admin_key or admin_key != expected_admin_key:
        logger.warning("Invalid admin key attempted")
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return True


def get_client_ip(request: Request) -> str:
    """
    Get client IP address from request
    """
    # Check for forwarded headers first
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fallback to request client
    if request.client:
        return request.client.host

    return "unknown"