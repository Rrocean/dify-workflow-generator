"""
Authentication and authorization module
Supports API keys, JWT tokens, and OAuth
"""
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field


try:
    from jose import JWTError, jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

try:
    from passlib.context import CryptContext
    PASSLIB_AVAILABLE = True
except ImportError:
    PASSLIB_AVAILABLE = False


@dataclass
class User:
    """User model"""
    id: str
    username: str
    email: str
    hashed_password: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    api_keys: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)


@dataclass
class APIKey:
    """API key model"""
    key: str
    user_id: str
    name: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    permissions: List[str] = field(default_factory=list)
    is_active: bool = True


class AuthManager:
    """Authentication manager"""

    SECRET_KEY = secrets.token_urlsafe(32)
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

    def __init__(self):
        self._users: Dict[str, User] = {}
        self._api_keys: Dict[str, APIKey] = {}
        self._pwd_context = None

        if PASSLIB_AVAILABLE:
            self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def _hash_password(self, password: str) -> str:
        """Hash a password"""
        if self._pwd_context:
            return self._pwd_context.hash(password)
        # Fallback to simple hash
        return hashlib.sha256(password.encode()).hexdigest()

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password"""
        if self._pwd_context:
            return self._pwd_context.verify(plain_password, hashed_password)
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        is_admin: bool = False
    ) -> User:
        """Create a new user"""
        user_id = secrets.token_hex(16)
        hashed_password = self._hash_password(password)

        user = User(
            id=user_id,
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_admin=is_admin
        )

        self._users[user_id] = user
        return user

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user"""
        for user in self._users.values():
            if user.username == username:
                if self._verify_password(password, user.hashed_password or ""):
                    return user
        return None

    def create_access_token(
        self,
        user_id: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT access token"""
        if not JWT_AVAILABLE:
            raise RuntimeError("JWT support not available. Install with: pip install python-jose")

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }

        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify a JWT token"""
        if not JWT_AVAILABLE:
            return None

        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return payload
        except JWTError:
            return None

    def create_api_key(
        self,
        user_id: str,
        name: str,
        expires_days: Optional[int] = None,
        permissions: Optional[List[str]] = None
    ) -> APIKey:
        """Create an API key for a user"""
        # Generate secure API key
        key = f"dw_{secrets.token_urlsafe(32)}"

        expires_at = None
        if expires_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_days)

        api_key = APIKey(
            key=key,
            user_id=user_id,
            name=name,
            expires_at=expires_at,
            permissions=permissions or []
        )

        self._api_keys[key] = api_key

        # Add to user's API keys
        if user_id in self._users:
            self._users[user_id].api_keys.append(key)

        return api_key

    def verify_api_key(self, key: str) -> Optional[APIKey]:
        """Verify an API key"""
        api_key = self._api_keys.get(key)

        if not api_key:
            return None

        if not api_key.is_active:
            return None

        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            return None

        # Update last used
        api_key.last_used = datetime.utcnow()

        return api_key

    def revoke_api_key(self, key: str, user_id: str) -> bool:
        """Revoke an API key"""
        api_key = self._api_keys.get(key)

        if not api_key or api_key.user_id != user_id:
            return False

        api_key.is_active = False
        return True

    def get_user_api_keys(self, user_id: str) -> List[APIKey]:
        """Get all API keys for a user"""
        keys = []
        for key, api_key in self._api_keys.items():
            if api_key.user_id == user_id:
                keys.append(api_key)
        return keys

    def check_permission(self, user: User, permission: str) -> bool:
        """Check if user has a permission"""
        if user.is_admin:
            return True
        return permission in user.permissions


# Global auth manager instance
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get or create global auth manager"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager
