"""Security utilities for authentication."""

from datetime import datetime, timedelta, timezone
from typing import Optional
import secrets
import hashlib
from jose import jwt, JWTError
from passlib.context import CryptContext
from src.config.auth import AuthConfig
from src.models.auth import TokenPayload


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityUtils:
    """Security utilities for authentication."""

    def __init__(self, config: AuthConfig):
        """Initialize security utilities with configuration."""
        self.config = config

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(
        self, user_id: str, session_id: Optional[str] = None
    ) -> str:
        """Create a JWT access token."""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.config.access_token_expire_minutes)
        jti = secrets.token_urlsafe(32)

        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": now,
            "jti": jti,
            "token_type": "access",
            "session_id": session_id,
        }

        return jwt.encode(
            payload, self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm
        )

    def create_refresh_token(self, user_id: str, session_id: str) -> str:
        """Create a JWT refresh token."""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=self.config.refresh_token_expire_days)
        jti = secrets.token_urlsafe(32)

        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": now,
            "jti": jti,
            "token_type": "refresh",
            "session_id": session_id,
        }

        return jwt.encode(
            payload, self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm
        )

    def decode_token(self, token: str) -> Optional[TokenPayload]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm],
            )
            return TokenPayload(**payload)
        except JWTError:
            return None

    def create_password_reset_token(self, user_id: str) -> str:
        """Create a password reset token."""
        token = secrets.token_urlsafe(32)
        # Hash the token for storage
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return token, token_hash

    def hash_token(self, token: str) -> str:
        """Hash a token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    def create_email_verification_token(self, user_id: str, email: str) -> str:
        """Create an email verification token."""
        token = secrets.token_urlsafe(32)
        # Hash the token for storage
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return token, token_hash

    def generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return secrets.token_urlsafe(32)

    def is_token_expired(self, token_payload: TokenPayload) -> bool:
        """Check if a token is expired."""
        now = datetime.now(timezone.utc)
        return token_payload.exp < now

    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash an API key for storage/lookup."""
        return hashlib.sha256(api_key.encode()).hexdigest()
