import os
import base64
from typing import Optional
import boto3
from botocore.config import Config


def _ensure_base64_digest(value: str) -> str:
    """Convert hex-encoded digests to base64 for S3 headers."""

    cleaned = value.strip()

    # Hex-encoded digests have even length and contain only hex characters
    is_hex = len(cleaned) % 2 == 0 and all(
        c in "0123456789abcdefABCDEF" for c in cleaned
    )
    if not is_hex:
        return cleaned

    # Convert hex string to base64
    raw_bytes = bytes.fromhex(cleaned)
    return base64.b64encode(raw_bytes).decode("ascii")


class StorageService:
    def __init__(self, bucket_name: Optional[str] = None) -> None:
        # Force SigV4 so modern headers like checksum are signed correctly
        region = (
            os.getenv("STORAGE_BUCKET_REGION")
            or os.getenv("AWS_REGION")
            or os.getenv("AWS_DEFAULT_REGION")
        )
        client_kwargs: dict = {"config": Config(signature_version="s3v4")}
        if region:
            client_kwargs["region_name"] = region
        self.client = boto3.client("s3", **client_kwargs)
        self.bucket_name = bucket_name or os.getenv("STORAGE_BUCKET_NAME")

    def generate_presigned_upload_url(
        self,
        key: str,
        md5: str,
        sha256: str,
        expires_in: int = 600,
        content_type: str | None = None,
    ) -> tuple[str, dict]:
        md5_b64 = _ensure_base64_digest(md5)
        sha256_b64 = _ensure_base64_digest(sha256)

        params = {
            "Bucket": self.bucket_name,
            "Key": key,
            "ContentMD5": md5_b64,  # signs the Content-MD5 header
            "ChecksumSHA256": sha256_b64,  # signs x-amz-checksum-sha256
        }

        if content_type:
            params["ContentType"] = content_type

        # Return the URL and the *required headers* the client must send
        required_headers = {
            "Content-MD5": md5_b64,
            "x-amz-checksum-sha256": sha256_b64,
        }
        if content_type:
            required_headers["Content-Type"] = content_type

        return self.client.generate_presigned_url(
            "put_object", Params=params, ExpiresIn=expires_in, HttpMethod="PUT"
        ), required_headers

    def generate_presigned_get_url(
        self,
        key: str,
        expires_in: int = 600,
    ) -> str:
        raise NotImplementedError()
