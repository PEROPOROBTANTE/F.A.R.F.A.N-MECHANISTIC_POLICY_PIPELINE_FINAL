"""
AtroZ Admin Authentication Module
Minimal but secure authentication for admin panel access
"""

import hashlib
import logging
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class AdminSession:
    """Represents an active admin session"""
    session_id: str
    username: str
    created_at: datetime
    last_activity: datetime
    ip_address: str

    def is_expired(self, timeout_minutes: int = 60) -> bool:
        """Check if session has expired"""
        return datetime.now() - self.last_activity > timedelta(minutes=timeout_minutes)

    def update_activity(self) -> None:
        """Update last activity timestamp"""
        self.last_activity = datetime.now()


class AdminAuthenticator:
    """
    Simple but secure authentication system for admin panel.

    Security features:
    - Password hashing with salt
    - Session management with timeout
    - Rate limiting on login attempts
    - IP-based session tracking
    """

    def __init__(self, session_timeout_minutes: int = 60) -> None:
        self.session_timeout = session_timeout_minutes
        self.sessions: dict[str, AdminSession] = {}
        self.login_attempts: dict[str, list] = {}

        # Default credentials (should be changed in production)
        # Default password: "atroz_admin_2024"
        self.users = {
            "admin": {
                "password_hash": self._hash_password("atroz_admin_2024", "default_salt"),
                "salt": "default_salt",
                "role": "administrator"
            }
        }

        logger.info("Admin authenticator initialized")

    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password with salt using SHA-256"""
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

    def _generate_session_id(self) -> str:
        """Generate secure random session ID"""
        return secrets.token_urlsafe(32)

    def _check_rate_limit(self, ip_address: str, max_attempts: int = 5, window_minutes: int = 15) -> bool:
        """Check if IP has exceeded login attempt rate limit"""
        now = time.time()
        window_seconds = window_minutes * 60

        if ip_address not in self.login_attempts:
            self.login_attempts[ip_address] = []

        # Remove old attempts outside window
        self.login_attempts[ip_address] = [
            timestamp for timestamp in self.login_attempts[ip_address]
            if now - timestamp < window_seconds
        ]

        # Check if too many attempts
        if len(self.login_attempts[ip_address]) >= max_attempts:
            logger.warning(f"Rate limit exceeded for IP: {ip_address}")
            return False

        return True

    def authenticate(self, username: str, password: str, ip_address: str) -> str | None:
        """
        Authenticate user and create session.

        Args:
            username: Username to authenticate
            password: Plain text password
            ip_address: IP address of client

        Returns:
            Session ID if authentication successful, None otherwise
        """
        # Check rate limit
        if not self._check_rate_limit(ip_address):
            return None

        # Record login attempt
        if ip_address in self.login_attempts:
            self.login_attempts[ip_address].append(time.time())
        else:
            self.login_attempts[ip_address] = [time.time()]

        # Check if user exists
        if username not in self.users:
            logger.warning(f"Login attempt for non-existent user: {username}")
            return None

        user = self.users[username]
        password_hash = self._hash_password(password, user["salt"])

        # Verify password
        if password_hash != user["password_hash"]:
            logger.warning(f"Failed login attempt for user: {username} from IP: {ip_address}")
            return None

        # Create session
        session_id = self._generate_session_id()
        self.sessions[session_id] = AdminSession(
            session_id=session_id,
            username=username,
            created_at=datetime.now(),
            last_activity=datetime.now(),
            ip_address=ip_address
        )

        logger.info(f"Successful login for user: {username} from IP: {ip_address}")
        return session_id

    def validate_session(self, session_id: str, ip_address: str | None = None) -> bool:
        """
        Validate if session is active and valid.

        Args:
            session_id: Session ID to validate
            ip_address: Optional IP address to verify session origin

        Returns:
            True if session is valid, False otherwise
        """
        if session_id not in self.sessions:
            return False

        session = self.sessions[session_id]

        # Check if expired
        if session.is_expired(self.session_timeout):
            logger.info(f"Session expired for user: {session.username}")
            del self.sessions[session_id]
            return False

        # Check IP if provided (optional security layer)
        if ip_address and session.ip_address != ip_address:
            logger.warning(f"IP mismatch for session: {session_id}")
            return False

        # Update activity
        session.update_activity()
        return True

    def get_session(self, session_id: str) -> AdminSession | None:
        """Get session details if valid"""
        if self.validate_session(session_id):
            return self.sessions[session_id]
        return None

    def logout(self, session_id: str) -> None:
        """Terminate session"""
        if session_id in self.sessions:
            username = self.sessions[session_id].username
            del self.sessions[session_id]
            logger.info(f"User logged out: {username}")

    def cleanup_expired_sessions(self) -> None:
        """Remove all expired sessions (should be called periodically)"""
        expired = [
            sid for sid, session in self.sessions.items()
            if session.is_expired(self.session_timeout)
        ]

        for sid in expired:
            del self.sessions[sid]

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")

    def add_user(self, username: str, password: str, role: str = "user") -> None:
        """Add new user (admin function)"""
        salt = secrets.token_hex(16)
        password_hash = self._hash_password(password, salt)

        self.users[username] = {
            "password_hash": password_hash,
            "salt": salt,
            "role": role
        }

        logger.info(f"New user added: {username} with role: {role}")

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        if username not in self.users:
            return False

        user = self.users[username]
        old_hash = self._hash_password(old_password, user["salt"])

        if old_hash != user["password_hash"]:
            logger.warning(f"Failed password change for user: {username}")
            return False

        # Generate new salt for additional security
        new_salt = secrets.token_hex(16)
        new_hash = self._hash_password(new_password, new_salt)

        self.users[username]["password_hash"] = new_hash
        self.users[username]["salt"] = new_salt

        logger.info(f"Password changed for user: {username}")
        return True


# Global authenticator instance
_authenticator: AdminAuthenticator | None = None


def get_authenticator() -> AdminAuthenticator:
    """Get or create global authenticator instance"""
    global _authenticator
    if _authenticator is None:
        _authenticator = AdminAuthenticator()
    return _authenticator


def require_auth(func):
    """Decorator for Flask routes requiring authentication"""
    from functools import wraps

    from flask import jsonify, request

    @wraps(func)
    def wrapper(*args, **kwargs):
        session_id = request.cookies.get('atroz_session')
        if not session_id:
            session_id = request.headers.get('X-Session-ID')

        if not session_id:
            return jsonify({"error": "Authentication required"}), 401

        auth = get_authenticator()
        ip_address = request.remote_addr

        if not auth.validate_session(session_id, ip_address):
            return jsonify({"error": "Invalid or expired session"}), 401

        return func(*args, **kwargs)

    return wrapper
