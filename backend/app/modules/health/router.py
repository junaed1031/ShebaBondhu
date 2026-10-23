from datetime import datetime, timezone
import logging
from typing import Any

from fastapi import APIRouter

from app.core.firebase import get_firestore_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Public health check endpoint returning service status,
    version, Firestore connectivity, and timestamp.
    """
    firestore_status = "connected"
    try:
        client = get_firestore_client()
        if client is None:
            firestore_status = "disconnected"
    except Exception as e:
        logger.warning("Firestore connectivity check failed: %s", e)
        firestore_status = "disconnected"

    return {
        "status": "ok",
        "version": "1.0.0",
        "firestore": firestore_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
