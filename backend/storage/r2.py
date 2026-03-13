import os
import threading

import boto3
from botocore.config import Config

_client = None
_lock = threading.Lock()


def _get_client():
    global _client
    if _client is None:
        with _lock:
            if _client is None:  # double-checked locking
                _client = boto3.client(
                    "s3",
                    endpoint_url=f"https://{os.getenv('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
                    aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
                    aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
                    config=Config(signature_version="s3v4"),
                    region_name="auto",
                )
    return _client


def generate_presigned_url(key: str, expires: int = 3600) -> str:
    return _get_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": os.getenv("R2_BUCKET_NAME"), "Key": key},
        ExpiresIn=expires,
    )


def download_object(key: str) -> bytes:
    """Download object from R2 and return its bytes."""
    resp = _get_client().get_object(
        Bucket=os.getenv("R2_BUCKET_NAME"),
        Key=key,
    )
    return resp["Body"].read()


def upload_object(key: str, data: bytes, content_type: str = "image/png") -> None:
    """Upload bytes to R2 at the given key."""
    _get_client().put_object(
        Bucket=os.getenv("R2_BUCKET_NAME"),
        Key=key,
        Body=data,
        ContentType=content_type,
    )
