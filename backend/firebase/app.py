"""
Firebase Admin SDK initialization.

Requires one of:
  FIREBASE_SERVICE_ACCOUNT_KEY=/path/to/serviceAccountKey.json  (local dev)
  or Application Default Credentials (production / Google Cloud)
"""
import os
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore, auth as fb_auth

_ROOT = Path(__file__).parent.parent.parent  # project root
_app = None


def _init():
    global _app
    if _app is not None:
        return
    sa_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
    if sa_path:
        resolved = Path(sa_path) if Path(sa_path).is_absolute() else _ROOT / sa_path
        cred = credentials.Certificate(resolved)
    else:
        cred = credentials.ApplicationDefault()
    _app = firebase_admin.initialize_app(cred)


def get_db():
    _init()
    return firestore.client()


def verify_token(id_token: str) -> dict:
    _init()
    return fb_auth.verify_id_token(id_token)
