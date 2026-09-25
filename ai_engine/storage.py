"""
Downloads CV PDFs from the PRIVATE MinIO bucket. The request is signed with
AWS Signature V4 (query-string / presigned form), which MinIO accepts, so no
extra package (boto3 / minio) is needed.
"""

import datetime
import hashlib
import hmac
from urllib.parse import quote, urlsplit

import requests

import config

REGION = "us-east-1"  # MinIO's default region
SERVICE = "s3"


def _sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def presigned_get_url(file_url: str, expires_seconds: int = 300) -> str:
    """Turns a stored object URL (http://any-host:9000/bucket/key) into a
    short-lived signed URL on the MinIO endpoint configured for this process
    (the stored host may be localhost for the ETL, minio inside Docker)."""
    endpoint = urlsplit(config.MINIO_ENDPOINT)
    host = endpoint.netloc
    canonical_uri = quote(urlsplit(file_url).path, safe="/-_.~")

    now = datetime.datetime.now(datetime.timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")
    scope = f"{date_stamp}/{REGION}/{SERVICE}/aws4_request"

    params = {
        "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
        "X-Amz-Credential": f"{config.MINIO_ACCESS_KEY}/{scope}",
        "X-Amz-Date": amz_date,
        "X-Amz-Expires": str(expires_seconds),
        "X-Amz-SignedHeaders": "host",
    }
    canonical_query = "&".join(
        f"{quote(k, safe='-_.~')}={quote(v, safe='-_.~')}" for k, v in sorted(params.items())
    )
    canonical_request = "\n".join([
        "GET", canonical_uri, canonical_query, f"host:{host}\n", "host", "UNSIGNED-PAYLOAD",
    ])
    string_to_sign = "\n".join([
        "AWS4-HMAC-SHA256", amz_date, scope,
        hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
    ])

    k_date = _sign(("AWS4" + config.MINIO_SECRET_KEY).encode("utf-8"), date_stamp)
    k_region = hmac.new(k_date, REGION.encode(), hashlib.sha256).digest()
    k_service = hmac.new(k_region, SERVICE.encode(), hashlib.sha256).digest()
    k_signing = hmac.new(k_service, b"aws4_request", hashlib.sha256).digest()
    signature = hmac.new(k_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    return f"{endpoint.scheme}://{host}{canonical_uri}?{canonical_query}&X-Amz-Signature={signature}"


def download_cv(file_url: str) -> bytes:
    response = requests.get(presigned_get_url(file_url), timeout=30)
    response.raise_for_status()
    return response.content
