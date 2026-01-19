"""S3-compatible storage utilities."""

import io
from typing import BinaryIO
from urllib.parse import urljoin

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import get_settings

settings = get_settings()


class StorageService:
    """Service for interacting with S3-compatible storage (MinIO)."""

    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=f"{'https' if settings.storage_use_ssl else 'http'}://{settings.storage_endpoint}",
            aws_access_key_id=settings.storage_access_key,
            aws_secret_access_key=settings.storage_secret_key,
            config=Config(signature_version="s3v4"),
        )
        self.bucket = settings.storage_bucket
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError:
            self.client.create_bucket(Bucket=self.bucket)

    def upload_file(
        self,
        file_obj: BinaryIO,
        key: str,
        content_type: str | None = None,
    ) -> str:
        """Upload a file to storage.

        Args:
            file_obj: File-like object to upload
            key: Storage key (path)
            content_type: MIME type of the file

        Returns:
            The storage key
        """
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        self.client.upload_fileobj(
            file_obj,
            self.bucket,
            key,
            ExtraArgs=extra_args,
        )
        return key

    def upload_bytes(
        self,
        data: bytes,
        key: str,
        content_type: str | None = None,
    ) -> str:
        """Upload bytes to storage."""
        return self.upload_file(io.BytesIO(data), key, content_type)

    def download_file(self, key: str) -> bytes:
        """Download a file from storage.

        Args:
            key: Storage key (path)

        Returns:
            File contents as bytes
        """
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()

    def download_to_file(self, key: str, file_obj: BinaryIO) -> None:
        """Download a file to a file-like object."""
        self.client.download_fileobj(self.bucket, key, file_obj)

    def delete_file(self, key: str) -> None:
        """Delete a file from storage."""
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def delete_prefix(self, prefix: str) -> None:
        """Delete all files with a given prefix."""
        paginator = self.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            if "Contents" in page:
                objects = [{"Key": obj["Key"]} for obj in page["Contents"]]
                self.client.delete_objects(
                    Bucket=self.bucket,
                    Delete={"Objects": objects},
                )

    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate a presigned URL for file access.

        Args:
            key: Storage key (path)
            expires_in: URL expiration time in seconds

        Returns:
            Presigned URL
        """
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    def file_exists(self, key: str) -> bool:
        """Check if a file exists in storage."""
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False

    def get_file_size(self, key: str) -> int:
        """Get the size of a file in bytes."""
        response = self.client.head_object(Bucket=self.bucket, Key=key)
        return response["ContentLength"]


# Singleton instance
_storage_service: StorageService | None = None


def get_storage_service() -> StorageService:
    """Get the storage service singleton."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
