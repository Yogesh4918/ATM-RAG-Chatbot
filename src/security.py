"""
Security Module — PIN validation, rate limiting, and access control.
PIN is NEVER spoken, logged, or stored in plaintext.
Framework-agnostic: works with any session backend (Flask, FastAPI, etc.).
"""

import bcrypt
import time
import secrets
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────
MAX_PIN_ATTEMPTS: int = 3
LOCKOUT_DURATION: int = 30       # seconds
SESSION_TIMEOUT: int = 120       # seconds (2 minutes)
DEFAULT_PIN: str = "1234"        # Default PIN for simulation
MAX_INPUT_LENGTH: int = 500      # Max characters for user text input
MAX_PIN_LENGTH: int = 4


def hash_pin(pin: str) -> bytes:
    """Hash a PIN using bcrypt. Returns the bcrypt hash bytes."""
    return bcrypt.hashpw(pin.encode("utf-8"), bcrypt.gensalt())


def verify_pin(entered_pin: str, pin_hash: bytes) -> bool:
    """
    Verify an entered PIN against a bcrypt hash.
    Returns True if correct, False otherwise.
    NEVER logs the PIN value.
    """
    if not entered_pin or len(entered_pin) != MAX_PIN_LENGTH or not entered_pin.isdigit():
        return False
    return bcrypt.checkpw(entered_pin.encode("utf-8"), pin_hash)


def is_locked(locked_until: float) -> bool:
    """Check if PIN entry is currently locked out."""
    return locked_until > time.time()


def get_lockout_remaining(locked_until: float) -> int:
    """Get remaining lockout time in seconds."""
    return max(0, int(locked_until - time.time()))


def check_session_timeout(last_activity: float, timeout: int = SESSION_TIMEOUT) -> bool:
    """
    Check if the session has timed out.
    Returns True if session is still valid, False if timed out.
    """
    return (time.time() - last_activity) <= timeout


def validate_pin_attempt(
    entered_pin: str,
    pin_hash: bytes,
    attempts: int,
    locked_until: float,
) -> Tuple[bool, int, float, str]:
    """
    Full PIN validation with lockout logic.

    Args:
        entered_pin: The PIN entered by the user
        pin_hash: bcrypt hash of the correct PIN
        attempts: Current number of failed attempts
        locked_until: Timestamp until which PIN entry is locked

    Returns:
        Tuple of (success, new_attempts, new_locked_until, message_key)
    """
    # Check lockout
    if is_locked(locked_until):
        remaining = get_lockout_remaining(locked_until)
        return False, attempts, locked_until, "pin_locked"

    # Auto-unlock expired lockout
    if locked_until > 0 and locked_until <= time.time():
        attempts = 0
        locked_until = 0

    # Validate format
    if not entered_pin or len(entered_pin) != MAX_PIN_LENGTH or not entered_pin.isdigit():
        return False, attempts, locked_until, "invalid_pin_format"

    # Verify against hash
    if verify_pin(entered_pin, pin_hash):
        logger.info("PIN verified successfully")
        return True, 0, 0, "pin_correct"
    else:
        attempts += 1
        logger.warning("Incorrect PIN attempt (%d/%d)", attempts, MAX_PIN_ATTEMPTS)
        if attempts >= MAX_PIN_ATTEMPTS:
            locked_until = time.time() + LOCKOUT_DURATION
            logger.warning("PIN locked out for %d seconds", LOCKOUT_DURATION)
            return False, attempts, locked_until, "pin_locked"
        return False, attempts, locked_until, "pin_incorrect"


def sanitize_input(text: str, max_length: int = MAX_INPUT_LENGTH) -> str:
    """Sanitize user text input — strip, truncate, remove control characters."""
    if not text:
        return ""
    # Remove control characters except newlines
    cleaned = "".join(c for c in text if c.isprintable() or c in ("\n", "\t"))
    return cleaned.strip()[:max_length]


def generate_session_token() -> str:
    """Generate a cryptographically secure session token."""
    return secrets.token_hex(16)
