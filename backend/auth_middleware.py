from functools import wraps
from flask import request, jsonify, g
from backend.firebase import verify_token


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Unauthorized"}), 401
        try:
            decoded = verify_token(auth_header[7:])
            g.uid = decoded["uid"]
            g.user_email = decoded.get("email", "")
        except Exception:
            return jsonify({"error": "Invalid or expired token"}), 401
        return f(*args, **kwargs)
    return decorated


def get_optional_uid() -> str | None:
    """Return the Firebase UID if a valid Bearer token is present, else None."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    try:
        decoded = verify_token(auth_header[7:])
        return decoded["uid"]
    except Exception:
        return None
