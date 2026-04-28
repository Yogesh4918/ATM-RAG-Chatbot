"""Tests for security module functions."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.security import hash_pin, verify_pin, sanitize_input, validate_pin_attempt


class TestPinHashing:
    def test_hash_returns_bytes(self):
        h = hash_pin("1234")
        assert isinstance(h, bytes)

    def test_verify_correct_pin(self):
        h = hash_pin("1234")
        assert verify_pin("1234", h) is True

    def test_verify_wrong_pin(self):
        h = hash_pin("1234")
        assert verify_pin("0000", h) is False

    def test_verify_invalid_format(self):
        h = hash_pin("1234")
        assert verify_pin("abc", h) is False
        assert verify_pin("", h) is False
        assert verify_pin("12345", h) is False


class TestSanitizeInput:
    def test_strips_whitespace(self):
        assert sanitize_input("  hello  ") == "hello"

    def test_truncates_long_input(self):
        result = sanitize_input("a" * 1000, max_length=100)
        assert len(result) == 100

    def test_removes_control_chars(self):
        result = sanitize_input("hello\x00world")
        assert "\x00" not in result

    def test_empty_input(self):
        assert sanitize_input("") == ""
        assert sanitize_input(None) == ""


class TestPinValidation:
    def test_correct_pin(self):
        h = hash_pin("1234")
        ok, attempts, locked, msg = validate_pin_attempt("1234", h, 0, 0)
        assert ok is True
        assert attempts == 0
        assert msg == "pin_correct"

    def test_wrong_pin_increments(self):
        h = hash_pin("1234")
        ok, attempts, locked, msg = validate_pin_attempt("0000", h, 0, 0)
        assert ok is False
        assert attempts == 1
        assert msg == "pin_incorrect"

    def test_lockout_after_max(self):
        h = hash_pin("1234")
        ok, attempts, locked, msg = validate_pin_attempt("0000", h, 2, 0)
        assert ok is False
        assert attempts == 3
        assert locked > 0
        assert msg == "pin_locked"
