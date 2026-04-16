"""
Security Module — PIN validation, session management, and access control.
PIN is NEVER spoken, logged, or stored in plaintext.
"""

import bcrypt
import time
import secrets
import streamlit as st


# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────
MAX_PIN_ATTEMPTS = 3
LOCKOUT_DURATION = 30  # seconds
SESSION_TIMEOUT = 120  # seconds (2 minutes)
DEFAULT_PIN = "1234"   # Default PIN for simulation


def _get_pin_hash() -> bytes:
    """Get the bcrypt hash of the default PIN. In production, this would come from a secure database."""
    return bcrypt.hashpw(DEFAULT_PIN.encode("utf-8"), bcrypt.gensalt())


def init_security_state():
    """Initialize security-related session state variables."""
    if "pin_hash" not in st.session_state:
        st.session_state.pin_hash = _get_pin_hash()
    if "pin_attempts" not in st.session_state:
        st.session_state.pin_attempts = 0
    if "pin_locked_until" not in st.session_state:
        st.session_state.pin_locked_until = 0
    if "pin_verified" not in st.session_state:
        st.session_state.pin_verified = False
    if "session_token" not in st.session_state:
        st.session_state.session_token = None
    if "last_activity" not in st.session_state:
        st.session_state.last_activity = time.time()
    if "card_inserted" not in st.session_state:
        st.session_state.card_inserted = False


def is_locked() -> bool:
    """Check if PIN entry is currently locked out."""
    if st.session_state.pin_locked_until > time.time():
        return True
    # Auto-unlock when lockout expires
    if st.session_state.pin_locked_until > 0 and st.session_state.pin_locked_until <= time.time():
        st.session_state.pin_locked_until = 0
        st.session_state.pin_attempts = 0
    return False


def get_lockout_remaining() -> int:
    """Get remaining lockout time in seconds."""
    remaining = st.session_state.pin_locked_until - time.time()
    return max(0, int(remaining))


def validate_pin(entered_pin: str) -> bool:
    """
    Validate the entered PIN against the stored hash.
    Returns True if correct, False otherwise.
    NEVER logs the PIN value.
    """
    if is_locked():
        return False

    # Validate PIN format (4 digits only)
    if not entered_pin or len(entered_pin) != 4 or not entered_pin.isdigit():
        return False

    # Check PIN against bcrypt hash
    is_correct = bcrypt.checkpw(
        entered_pin.encode("utf-8"),
        st.session_state.pin_hash
    )

    if is_correct:
        st.session_state.pin_verified = True
        st.session_state.pin_attempts = 0
        st.session_state.session_token = secrets.token_hex(16)
        st.session_state.last_activity = time.time()
        return True
    else:
        st.session_state.pin_attempts += 1
        if st.session_state.pin_attempts >= MAX_PIN_ATTEMPTS:
            st.session_state.pin_locked_until = time.time() + LOCKOUT_DURATION
        return False


def get_attempts_remaining() -> int:
    """Get the number of PIN attempts remaining."""
    return MAX_PIN_ATTEMPTS - st.session_state.pin_attempts


def check_session_timeout() -> bool:
    """
    Check if the session has timed out.
    Returns True if session is still valid, False if timed out.
    """
    if not st.session_state.get("pin_verified", False):
        return True  # No session to timeout

    elapsed = time.time() - st.session_state.get("last_activity", time.time())
    if elapsed > SESSION_TIMEOUT:
        end_session()
        return False
    return True


def refresh_activity():
    """Update the last activity timestamp."""
    st.session_state.last_activity = time.time()


def insert_card():
    """Simulate card insertion."""
    st.session_state.card_inserted = True
    st.session_state.pin_verified = False
    st.session_state.pin_attempts = 0
    st.session_state.pin_locked_until = 0
    st.session_state.session_token = None
    st.session_state.last_activity = time.time()


def end_session():
    """End the current session and clear all sensitive data."""
    st.session_state.pin_verified = False
    st.session_state.session_token = None
    st.session_state.card_inserted = False
    st.session_state.pin_attempts = 0
    st.session_state.pin_locked_until = 0
    st.session_state.last_activity = time.time()
    # Clear pending transaction state
    if "pending_action" in st.session_state:
        del st.session_state.pending_action
    if "pending_amount" in st.session_state:
        del st.session_state.pending_amount


def is_authenticated() -> bool:
    """Check if the user is currently authenticated (card inserted + PIN verified)."""
    return (
        st.session_state.get("card_inserted", False)
        and st.session_state.get("pin_verified", False)
        and st.session_state.get("session_token") is not None
    )
