import logging
import os
from typing import Any

import firebase_admin
from firebase_admin import credentials, firestore

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_firestore_client: Any = None


def initialize_firebase() -> firebase_admin.App:
    """Initialize Firebase Admin SDK once."""
    if firebase_admin._apps:
        return firebase_admin.get_app()

    settings = get_settings()
    cred_path = settings.GOOGLE_APPLICATION_CREDENTIALS

    options = {}
    if settings.FIREBASE_PROJECT_ID:
        options["projectId"] = settings.FIREBASE_PROJECT_ID

    if cred_path and os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        app = firebase_admin.initialize_app(cred, options=options or None)
    else:
        app = firebase_admin.initialize_app(options=options or None)

    logger.info("Firebase Admin SDK initialized.")
    return app


def get_firestore_client() -> Any:
    """Expose the Firestore client singleton."""
    global _firestore_client
    if _firestore_client is None:
        initialize_firebase()
        _firestore_client = firestore.client()
    return _firestore_client


def set_firestore_client(client: Any) -> None:
    """Allow overriding the Firestore client (e.g. for testing)."""
    global _firestore_client
    _firestore_client = client
