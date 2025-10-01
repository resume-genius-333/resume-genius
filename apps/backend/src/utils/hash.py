"""Hash-related utility helpers."""

from __future__ import annotations

import base64
import binascii
import re
from typing import Union

_SHA256_HEX_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
_MD5_HEX_PATTERN = re.compile(r"^[0-9a-fA-F]{32}$")


class SHA256:
    """Representation of a SHA-256 digest with base16/base64 helpers."""

    __slots__ = ("_bytes",)
    _DIGEST_LENGTH = 32

    def __init__(self, digest: Union[bytes, bytearray, memoryview]):
        data = bytes(digest)
        if len(data) != self._DIGEST_LENGTH:
            raise ValueError("SHA-256 digest must be exactly 32 bytes.")
        self._bytes = data

    @classmethod
    def from_hex(cls, value: str) -> "SHA256":
        """Create an instance from a hex-encoded digest."""
        hex_digest = cls._normalise_hex(value)
        return cls(bytes.fromhex(hex_digest))

    @classmethod
    def from_base64(cls, value: str) -> "SHA256":
        """Create an instance from a base64 (standard or URL-safe) digest."""
        base64_digest = cls._normalise_base64(value)
        try:
            data = base64.b64decode(base64_digest, validate=True)
        except binascii.Error as exc:
            raise ValueError("Invalid base64-encoded SHA-256 digest.") from exc

        if len(data) != cls._DIGEST_LENGTH:
            raise ValueError("Base64 digest does not decode to 32 bytes.")

        return cls(data)

    @classmethod
    def parse(cls, value: Union[str, bytes, bytearray, memoryview]) -> "SHA256":
        """Parse an input as either hex/base64 string or raw bytes."""
        if isinstance(value, (bytes, bytearray, memoryview)):
            return cls(value)

        if not isinstance(value, str):
            raise TypeError("SHA256.parse expects str or bytes-like input.")

        candidate = value.strip()
        if not candidate:
            raise ValueError("SHA-256 digest must be a non-empty string.")

        if len(candidate) == 64 and _SHA256_HEX_PATTERN.fullmatch(candidate):
            return cls.from_hex(candidate)

        return cls.from_base64(candidate)

    def b64(self, url_safe: bool) -> str:
        """Return the digest encoded as URL-safe base64 (with padding)."""
        if url_safe:
            return base64.urlsafe_b64encode(self._bytes).decode("ascii")
        else:
            return base64.b64encode(self._bytes).decode("ascii")

    @property
    def hex(self) -> str:
        """Return the digest encoded as lowercase hex."""
        return self._bytes.hex()

    def __bytes__(self) -> bytes:  # pragma: no cover - simple passthrough
        return self._bytes

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SHA256):
            return self._bytes == other._bytes
        return NotImplemented

    def __hash__(self) -> int:  # pragma: no cover - trivial wrapper
        return hash(self._bytes)

    def __repr__(self) -> str:
        return self.b64(url_safe=False)

    def __str__(self) -> str:
        return self.b64(url_safe=True)

    @staticmethod
    def _normalise_hex(value: str) -> str:
        if value is None:
            raise ValueError("SHA-256 hex digest must be provided.")

        candidate = value.strip()
        if not candidate:
            raise ValueError("SHA-256 hex digest must be a non-empty string.")

        if len(candidate) != 64 or not _SHA256_HEX_PATTERN.fullmatch(candidate):
            raise ValueError("SHA-256 hex digest must be 64 hexadecimal characters.")

        return candidate.lower()

    @staticmethod
    def _normalise_base64(value: str) -> str:
        if value is None:
            raise ValueError("SHA-256 base64 digest must be provided.")

        candidate = "".join(value.split())
        if not candidate:
            raise ValueError("SHA-256 base64 digest must be a non-empty string.")

        # Accept URL-safe base64 by translating to standard alphabet.
        candidate = candidate.replace("-", "+").replace("_", "/")

        missing_padding = len(candidate) % 4
        if missing_padding:
            candidate += "=" * (4 - missing_padding)

        return candidate


class MD5:
    """Representation of an MD5 digest with base16/base64 helpers."""

    __slots__ = ("_bytes",)
    _DIGEST_LENGTH = 16

    def __init__(self, digest: Union[bytes, bytearray, memoryview]):
        data = bytes(digest)
        if len(data) != self._DIGEST_LENGTH:
            raise ValueError("MD5 digest must be exactly 16 bytes.")
        self._bytes = data

    @classmethod
    def from_hex(cls, value: str) -> "MD5":
        """Create an instance from a hex-encoded digest."""
        hex_digest = cls._normalise_hex(value)
        return cls(bytes.fromhex(hex_digest))

    @classmethod
    def from_base64(cls, value: str) -> "MD5":
        """Create an instance from a base64 (standard or URL-safe) digest."""
        base64_digest = cls._normalise_base64(value)
        try:
            data = base64.b64decode(base64_digest, validate=True)
        except binascii.Error as exc:
            raise ValueError("Invalid base64-encoded MD5 digest.") from exc

        if len(data) != cls._DIGEST_LENGTH:
            raise ValueError("Base64 digest does not decode to 16 bytes.")

        return cls(data)

    @classmethod
    def parse(cls, value: Union[str, bytes, bytearray, memoryview]) -> "MD5":
        """Parse an input as either hex/base64 string or raw bytes."""
        if isinstance(value, (bytes, bytearray, memoryview)):
            return cls(value)

        if not isinstance(value, str):
            raise TypeError("MD5.parse expects str or bytes-like input.")

        candidate = value.strip()
        if not candidate:
            raise ValueError("MD5 digest must be a non-empty string.")

        if len(candidate) == 32 and _MD5_HEX_PATTERN.fullmatch(candidate):
            return cls.from_hex(candidate)

        return cls.from_base64(candidate)

    def b64(self, url_safe: bool) -> str:
        """Return the digest encoded as URL-safe base64 (with padding)."""
        if url_safe:
            return base64.urlsafe_b64encode(self._bytes).decode("ascii")
        else:
            return base64.b64encode(self._bytes).decode("ascii")

    @property
    def hex(self) -> str:
        """Return the digest encoded as lowercase hex."""
        return self._bytes.hex()

    def __bytes__(self) -> bytes:  # pragma: no cover - simple passthrough
        return self._bytes

    def __eq__(self, other: object) -> bool:
        if isinstance(other, MD5):
            return self._bytes == other._bytes
        return NotImplemented

    def __hash__(self) -> int:  # pragma: no cover - trivial wrapper
        return hash(self._bytes)

    def __repr__(self) -> str:
        return self.b64(url_safe=False)

    def __str__(self) -> str:
        return self.b64(url_safe=True)

    @staticmethod
    def _normalise_hex(value: str) -> str:
        if value is None:
            raise ValueError("MD5 hex digest must be provided.")

        candidate = value.strip()
        if not candidate:
            raise ValueError("MD5 hex digest must be a non-empty string.")

        if len(candidate) != 32 or not _MD5_HEX_PATTERN.fullmatch(candidate):
            raise ValueError("MD5 hex digest must be 32 hexadecimal characters.")

        return candidate.lower()

    @staticmethod
    def _normalise_base64(value: str) -> str:
        if value is None:
            raise ValueError("MD5 base64 digest must be provided.")

        candidate = "".join(value.split())
        if not candidate:
            raise ValueError("MD5 base64 digest must be a non-empty string.")

        candidate = candidate.replace("-", "+").replace("_", "/")

        missing_padding = len(candidate) % 4
        if missing_padding:
            candidate += "=" * (4 - missing_padding)

        return candidate


class HashUtils:
    """Utility functions for working with hash values."""

    @staticmethod
    def validate_sha256(value: str) -> SHA256:
        """Validate input and return the parsed SHA-256 digest object."""
        return SHA256.parse(value)

    @staticmethod
    def validate_md5(value: str) -> MD5:
        """Validate input and return the parsed MD5 digest object."""
        return MD5.parse(value)
