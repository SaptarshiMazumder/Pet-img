import os
from functools import wraps

import jwt
from jwt import PyJWKClient
from flask import request, jsonify, g

_AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN", "dev-xiwa5ogu3vfhcfba.us.auth0.com")
_AUTH0_CLIENT_ID = os.environ.get("AUTH0_CLIENT_ID", "glHmYjs0pbowPZAtSKaQty4VJjvJnQgO")
_jwks_client = PyJWKClient(f"https://{_AUTH0_DOMAIN}/.well-known/jwks.json")


def _verify_token(token: str) -> dict:
    signing_key = _jwks_client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=_AUTH0_CLIENT_ID,
        issuer=f"https://{_AUTH0_DOMAIN}/",
    )


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Unauthorized"}), 401
        try:
            decoded = _verify_token(auth_header[7:])
            g.uid = decoded["sub"]
            g.user_email = decoded.get("email", "")
        except Exception:
            return jsonify({"error": "Invalid or expired token"}), 401
        return f(*args, **kwargs)
    return decorated


def get_optional_uid() -> str | None:
    """Return the Auth0 user sub if a valid Bearer token is present, else None."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    try:
        decoded = _verify_token(auth_header[7:])
        return decoded["sub"]
    except Exception:
        return None
