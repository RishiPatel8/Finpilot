import os
import json
import logging
from typing import Dict, Any, Optional
import firebase_admin
from firebase_admin import auth as fb_auth, credentials
from app.core.config import settings

logger = logging.getLogger("finpilot.firebase")

_firebase_app: Optional[firebase_admin.App] = None


def get_firebase_app() -> Optional[firebase_admin.App]:
    """Initializes or retrieves the Firebase Admin App."""
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    if not firebase_admin._apps:
        try:
            if settings.FIREBASE_CREDENTIALS_PATH and os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                _firebase_app = firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin initialized via credentials file.")
            elif settings.FIREBASE_CREDENTIALS_JSON:
                cred_dict = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
                cred = credentials.Certificate(cred_dict)
                _firebase_app = firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin initialized via JSON credentials string.")
            elif settings.FIREBASE_PROJECT_ID:
                _firebase_app = firebase_admin.initialize_app(options={"projectId": settings.FIREBASE_PROJECT_ID})
                logger.info(f"Firebase Admin initialized with Project ID: {settings.FIREBASE_PROJECT_ID}")
        except Exception as e:
            logger.warning(f"Firebase Admin initialization deferred/failed: {e}")
            _firebase_app = None
    else:
        _firebase_app = firebase_admin.get_app()

    return _firebase_app


def verify_firebase_id_token(id_token: str) -> Dict[str, Any]:
    """
    Verifies Firebase ID token server-side.
    Validates token signature, issuer, audience, expiry, and revocation.
    Includes mock/test token handling for local test suite and offline environments.
    """
    if not id_token:
        raise ValueError("Firebase ID token cannot be empty.")

    # Test / Mock Token Handling for CI and Offline Development
    if id_token.startswith("mock-firebase:"):
        # Format: mock-firebase:UID:EMAIL:NAME
        parts = id_token.split(":")
        uid = parts[1] if len(parts) > 1 else "mock_uid_123"
        email = parts[2] if len(parts) > 2 else "mockuser@example.com"
        name = parts[3] if len(parts) > 3 else "Mock Firebase User"
        return {
            "uid": uid,
            "email": email,
            "name": name,
            "email_verified": True,
            "firebase": {"sign_in_provider": "google.com"}
        }

    app = get_firebase_app()
    if not app:
        raise ValueError("Firebase Admin is not configured. Set FIREBASE_PROJECT_ID or credentials.")

    try:
        decoded_token = fb_auth.verify_id_token(id_token, check_revoked=True, app=app)
        return decoded_token
    except Exception as e:
        logger.error(f"Failed to verify Firebase ID token: {e}")
        raise ValueError(f"Invalid or expired Firebase ID token: {str(e)}")
