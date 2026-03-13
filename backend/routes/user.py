from flask import Blueprint, jsonify, g

from backend.auth_middleware import require_auth
from backend.db import portrait_generation as generations_db
from backend.storage import generate_presigned_url

user_bp = Blueprint("user", __name__, url_prefix="/user")


@user_bp.get("/generations")
@require_auth
def get_generations():
    """Return the authenticated user's generation history with fresh presigned URLs."""
    docs = generations_db.get_by_uid(g.uid)

    results = []
    for doc in docs:
        data = doc.to_dict()
        r2_key = data.get("r2_key")
        presigned_url = None
        if r2_key:
            try:
                presigned_url = generate_presigned_url(r2_key, expires=3600)
            except Exception:
                pass
        ts = data.get("created_at")
        results.append({
            "job_id": doc.id,
            "template_key": data.get("template_key"),
            "style_key": data.get("style_key"),
            "positive_prompt": data.get("positive_prompt"),
            "seed": data.get("seed"),
            "r2_key": r2_key,
            "presigned_url": presigned_url,
            "created_at": ts.isoformat() if ts else None,
        })

    results.sort(key=lambda x: x["created_at"] or "", reverse=True)
    return jsonify({"generations": results})
