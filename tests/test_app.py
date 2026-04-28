"""
Tests for Smart ATM Flask API endpoints.
Run: python -m pytest tests/ -v
"""

import pytest
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app


@pytest.fixture
def client():
    """Create a Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestIndex:
    def test_serves_html(self, client):
        res = client.get("/")
        assert res.status_code == 200
        assert b"Smart ATM" in res.data

    def test_security_headers(self, client):
        res = client.get("/")
        assert res.headers.get("X-Content-Type-Options") == "nosniff"
        assert res.headers.get("X-Frame-Options") == "DENY"
        assert "Content-Security-Policy" in res.headers


class TestSessionStatus:
    def test_returns_session(self, client):
        res = client.get("/api/session-status")
        data = json.loads(res.data)
        assert "card_inserted" in data
        assert "languages" in data
        assert data["language"] == "English"


class TestInsertCard:
    def test_insert_card(self, client):
        res = client.post("/api/insert-card", json={})
        data = json.loads(res.data)
        assert data["success"] is True
        assert len(data["message"]) > 0


class TestSetLanguage:
    def test_change_language(self, client):
        res = client.post("/api/set-language", json={"language": "Hindi"})
        data = json.loads(res.data)
        assert data["success"] is True
        assert data["language"] == "Hindi"

    def test_invalid_language_ignored(self, client):
        client.post("/api/set-language", json={"language": "Hindi"})
        res = client.post("/api/set-language", json={"language": "Klingon"})
        data = json.loads(res.data)
        assert data["language"] == "Hindi"


class TestValidatePin:
    def test_correct_pin(self, client):
        client.post("/api/insert-card", json={})
        res = client.post("/api/validate-pin", json={"pin": "1234"})
        data = json.loads(res.data)
        assert data["success"] is True
        assert data["authenticated"] is True

    def test_incorrect_pin(self, client):
        client.post("/api/insert-card", json={})
        res = client.post("/api/validate-pin", json={"pin": "0000"})
        data = json.loads(res.data)
        assert data["success"] is False

    def test_invalid_pin_format(self, client):
        client.post("/api/insert-card", json={})
        res = client.post("/api/validate-pin", json={"pin": "abc"})
        data = json.loads(res.data)
        assert data["success"] is False

    def test_lockout_after_max_attempts(self, client):
        client.post("/api/insert-card", json={})
        for _ in range(3):
            client.post("/api/validate-pin", json={"pin": "0000"})
        res = client.post("/api/validate-pin", json={"pin": "0000"})
        data = json.loads(res.data)
        assert data["success"] is False
        assert data.get("locked") is True


class TestProcess:
    def test_greeting(self, client):
        client.post("/api/insert-card", json={})
        res = client.post("/api/process", json={"text": "hello"})
        data = json.loads(res.data)
        assert data["type"] == "greeting"

    def test_goodbye(self, client):
        client.post("/api/insert-card", json={})
        res = client.post("/api/process", json={"text": "bye"})
        data = json.loads(res.data)
        assert data["type"] == "goodbye"

    def test_balance_needs_pin(self, client):
        client.post("/api/insert-card", json={})
        res = client.post("/api/process", json={"text": "check balance"})
        data = json.loads(res.data)
        assert data["type"] == "need_pin"

    def test_balance_after_auth(self, client):
        client.post("/api/insert-card", json={})
        client.post("/api/validate-pin", json={"pin": "1234"})
        res = client.post("/api/process", json={"text": "check balance"})
        data = json.loads(res.data)
        assert data["type"] == "balance"
        assert "balance" in data

    def test_empty_input(self, client):
        client.post("/api/insert-card", json={})
        res = client.post("/api/process", json={"text": ""})
        data = json.loads(res.data)
        assert data["type"] == "error"

    def test_faq_query(self, client):
        client.post("/api/insert-card", json={})
        res = client.post("/api/process", json={"text": "what are the ATM safety tips"})
        data = json.loads(res.data)
        assert data["type"] in ("faq", "help")
        assert len(data["message"]) > 0


class TestWithdraw:
    def test_withdraw_needs_pin(self, client):
        client.post("/api/insert-card", json={})
        res = client.post("/api/withdraw", json={"amount": 500})
        data = json.loads(res.data)
        assert data["type"] == "need_pin"

    def test_withdraw_success(self, client):
        client.post("/api/insert-card", json={})
        client.post("/api/validate-pin", json={"pin": "1234"})
        res = client.post("/api/withdraw", json={"amount": 500})
        data = json.loads(res.data)
        assert data["type"] == "withdraw_success"
        assert data["receipt"]["amount"] == 500

    def test_withdraw_invalid_amount(self, client):
        client.post("/api/insert-card", json={})
        client.post("/api/validate-pin", json={"pin": "1234"})
        res = client.post("/api/withdraw", json={"amount": 150})
        data = json.loads(res.data)
        assert data["type"] == "error"


class TestTranslations:
    def test_returns_english(self, client):
        res = client.get("/api/translations?language=English")
        data = json.loads(res.data)
        assert "welcome" in data
        assert "withdraw" in data

    def test_returns_hindi(self, client):
        res = client.get("/api/translations?language=Hindi")
        data = json.loads(res.data)
        assert "welcome" in data
        assert data["select_language"] == "भाषा चुनें"

    def test_all_languages_have_keys(self, client):
        for lang in ["English", "Hindi", "Gujarati", "Marathi", "Tamil", "Telugu", "Bengali"]:
            res = client.get(f"/api/translations?language={lang}")
            data = json.loads(res.data)
            for key in ["welcome", "withdraw", "balance", "mini_statement", "session_status",
                         "no_card_status", "card_inserted_status", "cancel"]:
                assert key in data, f"Missing '{key}' in {lang}"


class TestEndSession:
    def test_end_session(self, client):
        client.post("/api/insert-card", json={})
        res = client.post("/api/end-session", json={})
        data = json.loads(res.data)
        assert data["success"] is True
