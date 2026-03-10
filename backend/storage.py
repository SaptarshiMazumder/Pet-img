import os

import boto3
from botocore.config import Config


def _r2_client():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{os.getenv('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
        aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def generate_presigned_url(key: str, expires: int = 3600) -> str:
    client = _r2_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": os.getenv("R2_BUCKET_NAME"), "Key": key},
        ExpiresIn=expires,
    )
