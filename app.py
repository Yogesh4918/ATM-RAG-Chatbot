"""
╔══════════════════════════════════════════════════════════════╗
║  Smart ATM Chatbot — Flask Backend + API                    ║
║  Serves the frontend and provides REST API endpoints        ║
║  Integrates Google Gemini AI for intelligent responses      ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import io
import uuid
import time
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
import random
import re

from flask import Flask, render_template, request, jsonify, session, send_file
from dotenv import load_dotenv

load_dotenv()

# ── Logging Setup ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("smart_atm")

# ── App Setup ──
app = Flask(__name__,
            template_folder="templates",
            static_folder="static")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,  # Set True in production with HTTPS
)

BASE_DIR = Path(__file__).parent

# ── Import application modules ──
from src.translations import LANGUAGES, UI_TEXT, get_text
from src.security import (
    hash_pin, verify_pin, sanitize_input,
    MAX_PIN_ATTEMPTS, LOCKOUT_DURATION, MAX_PIN_LENGTH,
)
from src.transaction_engine import (
    generate_mock_history, format_currency,
    INITIAL_BALANCE, DAILY_WITHDRAWAL_LIMIT, PER_TRANSACTION_LIMIT,
)
from src.rag_engine import keyword_search, query_rag, load_knowledge_base
from src.nlp_engine import classify_intent, extract_amount

# ═══════════════════════════════════════════════════════════
# Security Headers
# ═══════════════════════════════════════════════════════════
@app.after_request
def add_security_headers(response):
    """Add security headers to every response."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' https://fonts.googleapis.com 'unsafe-inline'; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "media-src 'self' blob:; "
    )
    return response

# ═══════════════════════════════════════════════════════════
# In-Memory Session Store
# ═══════════════════════════════════════════════════════════
sessions: dict = {}

# Pre-hash the default PIN with bcrypt (done once at startup)
DEFAULT_PIN = "1234"
DEFAULT_PIN_HASH = hash_pin(DEFAULT_PIN)

SESSION_TIMEOUT = 120  # seconds
RATE_LIMIT_WINDOW = 60  # seconds
MAX_PIN_REQUESTS = 10   # max PIN attempts per minute per session

# Pre-load knowledge base at startup
_kb = load_knowledge_base()
logger.info("Smart ATM started — Knowledge base: %d entries, Languages: %d",
            len(_kb), len(LANGUAGES))


def get_session():
    """Get or create a session."""
    sid = session.get("sid")
    if not sid or sid not in sessions:
        sid = str(uuid.uuid4())
        session["sid"] = sid
        sessions[sid] = create_fresh_session()
        logger.info("New session created: %s", sid[:8])
    s = sessions[sid]
    # Check timeout
    if s["card_inserted"] and s["pin_verified"]:
        if time.time() - s["last_activity"] > SESSION_TIMEOUT:
            lang = s["language"]
            sessions[sid] = create_fresh_session()
            sessions[sid]["language"] = lang
            logger.info("Session timed out: %s", sid[:8])
            return sessions[sid], True  # timed out
    s["last_activity"] = time.time()
    return s, False


def create_fresh_session() -> dict:
    """Create a new empty session state."""
    history = generate_mock_history()
    return {
        "card_inserted": False,
        "pin_verified": False,
        "pin_attempts": 0,
        "pin_locked_until": 0,
        "pin_request_times": [],
        "language": "English",
        "balance": INITIAL_BALANCE,
        "daily_withdrawn": 0,
        "last_withdrawal_date": None,
        "transaction_history": history,
        "card_number": "XXXX-XXXX-XXXX-1234",
        "last_activity": time.time(),
        "pending_action": None,
        "pending_amount": None,
        "chat_history": [],
    }


def cleanup_stale_sessions():
    """Remove sessions inactive for more than 10 minutes."""
    cutoff = time.time() - 600
    stale = [sid for sid, s in sessions.items() if s["last_activity"] < cutoff]
    for sid in stale:
        del sessions[sid]
    if stale:
        logger.info("Cleaned up %d stale sessions", len(stale))


def check_rate_limit(s: dict) -> bool:
    """Check if PIN request rate limit is exceeded."""
    now = time.time()
    s["pin_request_times"] = [t for t in s.get("pin_request_times", [])
                               if now - t < RATE_LIMIT_WINDOW]
    if len(s["pin_request_times"]) >= MAX_PIN_REQUESTS:
        return False  # rate limited
    s["pin_request_times"].append(now)
    return True


def t(s: dict, key: str, **kwargs) -> str:
    """Get translated text."""
    return get_text(s["language"], key, **kwargs)


# ═══════════════════════════════════════════════════════════
# API Routes
# ═══════════════════════════════════════════════════════════
@app.route("/")
def index():
    """Serve the main ATM frontend."""
    cleanup_stale_sessions()
    return render_template("index.html", languages=LANGUAGES)


@app.route("/api/session-status")
def session_status():
    """Return current session state."""
    s, timed_out = get_session()
    return jsonify({
        "card_inserted": s["card_inserted"],
        "pin_verified": s["pin_verified"],
        "language": s["language"],
        "balance": s["balance"],
        "card_number": s["card_number"],
        "timed_out": timed_out,
        "languages": {k: v for k, v in LANGUAGES.items()},
    })


@app.route("/api/insert-card", methods=["POST"])
def insert_card():
    """Simulate card insertion."""
    s, _ = get_session()
    s["card_inserted"] = True
    s["pin_verified"] = False
    s["pin_attempts"] = 0
    s["pin_locked_until"] = 0
    s["last_activity"] = time.time()
    welcome = t(s, "welcome")
    s["chat_history"].append({
        "role": "bot", "content": welcome,
        "time": datetime.now().strftime("%H:%M"),
    })
    logger.info("Card inserted")
    return jsonify({"success": True, "message": welcome})


@app.route("/api/set-language", methods=["POST"])
def set_language():
    """Change the UI language."""
    s, _ = get_session()
    lang = request.json.get("language", "English") if request.json else "English"
    # Validate language is in allowed list
    if lang in LANGUAGES:
        s["language"] = lang
        logger.info("Language changed to: %s", lang)
    return jsonify({"success": True, "language": s["language"]})


@app.route("/api/validate-pin", methods=["POST"])
def validate_pin_endpoint():
    """Validate PIN entry with rate limiting and lockout."""
    s, _ = get_session()

    # Rate limiting
    if not check_rate_limit(s):
        logger.warning("PIN rate limit exceeded")
        return jsonify({"success": False, "message": "Too many requests. Please wait."}), 429

    pin = request.json.get("pin", "") if request.json else ""

    # Check lockout
    if s["pin_locked_until"] > time.time():
        remaining = int(s["pin_locked_until"] - time.time())
        return jsonify({
            "success": False, "locked": True, "remaining": remaining,
            "message": t(s, "pin_locked"),
        })

    # Auto-unlock expired lockout
    if s["pin_locked_until"] > 0 and s["pin_locked_until"] <= time.time():
        s["pin_locked_until"] = 0
        s["pin_attempts"] = 0

    # Validate PIN format
    if not pin or len(pin) != MAX_PIN_LENGTH or not pin.isdigit():
        return jsonify({"success": False, "message": "Invalid PIN format"})

    # Verify PIN using bcrypt
    if verify_pin(pin, DEFAULT_PIN_HASH):
        s["pin_verified"] = True
        s["pin_attempts"] = 0
        s["last_activity"] = time.time()
        msg = t(s, "pin_correct")
        logger.info("PIN verified successfully")

        result = {"success": True, "message": msg, "authenticated": True}
        # Execute pending action
        if s.get("pending_action"):
            tx_result = execute_action(s, s["pending_action"], s.get("pending_amount"))
            result["action_result"] = tx_result
            s["pending_action"] = None
            s["pending_amount"] = None
        return jsonify(result)
    else:
        s["pin_attempts"] += 1
        logger.warning("Incorrect PIN attempt (%d/%d)", s["pin_attempts"], MAX_PIN_ATTEMPTS)
        if s["pin_attempts"] >= MAX_PIN_ATTEMPTS:
            s["pin_locked_until"] = time.time() + LOCKOUT_DURATION
            return jsonify({
                "success": False, "locked": True, "remaining": LOCKOUT_DURATION,
                "message": t(s, "pin_locked"),
            })
        remaining = MAX_PIN_ATTEMPTS - s["pin_attempts"]
        return jsonify({
            "success": False, "locked": False,
            "message": f"{t(s, 'pin_incorrect')} {t(s, 'attempts_remaining', n=remaining)}",
        })


@app.route("/api/process", methods=["POST"])
def process_input():
    """Process user text/voice input through NLP pipeline."""
    s, timed_out = get_session()
    if timed_out:
        return jsonify({"type": "timeout", "message": t(s, "session_timeout")})

    raw_text = request.json.get("text", "") if request.json else ""
    text = sanitize_input(raw_text)
    if not text:
        return jsonify({"type": "error", "message": "Empty input"})

    s["last_activity"] = time.time()
    result = classify_intent(text, s["language"])
    intent = result["intent"]
    amount = result.get("entities", {}).get("amount") or result.get("amount")

    # Greeting
    if intent == "greeting":
        msg = t(s, "welcome")
        return jsonify({"type": "greeting", "message": msg})

    # Goodbye
    if intent == "goodbye":
        msg = t(s, "goodbye")
        lang = s["language"]
        sid = session.get("sid")
        if sid:
            sessions[sid] = create_fresh_session()
            sessions[sid]["language"] = lang
        return jsonify({"type": "goodbye", "message": msg})

    # Transaction intents
    if intent in ("withdraw", "balance", "mini_statement"):
        if not s["pin_verified"]:
            s["pending_action"] = intent
            s["pending_amount"] = amount
            return jsonify({
                "type": "need_pin",
                "message": t(s, "enter_pin"),
                "intent": intent,
            })
        return jsonify(execute_action(s, intent, amount))

    # FAQ / Unknown → RAG pipeline (Gemini + keyword search)
    answer = query_rag(text, s["language"])
    if answer:
        return jsonify({"type": "faq", "message": answer})

    return jsonify({"type": "help", "message": t(s, "ask_anything")})


def execute_action(s: dict, intent: str, amount=None) -> dict:
    """Execute a banking action."""
    if intent == "balance":
        msg = t(s, "balance_result", balance=format_currency(s["balance"]))
        return {
            "type": "balance", "message": msg,
            "balance": s["balance"],
            "formatted_balance": format_currency(s["balance"]),
        }

    elif intent == "mini_statement":
        txns = s["transaction_history"][-5:]
        msg = t(s, "mini_statement")
        return {
            "type": "mini_statement", "message": msg,
            "transactions": txns,
            "balance": s["balance"],
            "formatted_balance": format_currency(s["balance"]),
            "card_number": s["card_number"],
        }

    elif intent == "withdraw":
        if amount is None:
            return {"type": "need_amount", "message": t(s, "enter_amount")}

        if amount <= 0 or amount % 100 != 0:
            return {"type": "error", "message": t(s, "invalid_amount")}
        if amount > PER_TRANSACTION_LIMIT:
            return {"type": "error", "message": t(s, "exceed_limit", limit=format_currency(PER_TRANSACTION_LIMIT))}

        today = datetime.now().date()
        if s.get("last_withdrawal_date") != str(today):
            s["daily_withdrawn"] = 0
        if s["daily_withdrawn"] + amount > DAILY_WITHDRAWAL_LIMIT:
            rem = DAILY_WITHDRAWAL_LIMIT - s["daily_withdrawn"]
            return {"type": "error", "message": t(s, "exceed_limit", limit=format_currency(rem))}
        if amount > s["balance"]:
            return {"type": "error", "message": t(s, "insufficient_funds", balance=format_currency(s["balance"]))}

        # Process withdrawal
        s["balance"] -= amount
        s["daily_withdrawn"] += amount
        s["last_withdrawal_date"] = str(today)
        ref = f"ATM{random.randint(100000, 999999)}"
        tx = {
            "date": datetime.now().strftime("%d-%b-%Y %H:%M"),
            "type": "Debit",
            "description": "ATM Cash Withdrawal",
            "amount": amount,
            "balance": s["balance"],
        }
        s["transaction_history"].append(tx)
        logger.info("Withdrawal: amount=%s, ref=%s", format_currency(amount), ref)

        receipt = {
            "card_number": s["card_number"],
            "date_time": datetime.now().strftime("%d-%b-%Y %H:%M:%S"),
            "transaction_type": "Cash Withdrawal",
            "amount": amount,
            "formatted_amount": format_currency(amount),
            "available_balance": s["balance"],
            "formatted_balance": format_currency(s["balance"]),
            "reference_no": ref,
        }
        msg = t(s, "withdraw_success", amount=format_currency(amount))
        return {
            "type": "withdraw_success", "message": msg,
            "receipt": receipt,
            "collect_msg": t(s, "collect_cash"),
        }

    return {"type": "error", "message": "Unknown action"}


@app.route("/api/withdraw", methods=["POST"])
def api_withdraw():
    """Direct withdrawal endpoint."""
    s, _ = get_session()
    if not s["pin_verified"]:
        return jsonify({"type": "need_pin", "message": t(s, "enter_pin")})
    raw_amount = request.json.get("amount", 0) if request.json else 0
    try:
        amount = int(raw_amount)
    except (ValueError, TypeError):
        return jsonify({"type": "error", "message": t(s, "invalid_amount")})
    result = execute_action(s, "withdraw", amount)
    return jsonify(result)


@app.route("/api/end-session", methods=["POST"])
def end_session_api():
    """End the current ATM session."""
    s, _ = get_session()
    msg = t(s, "goodbye")
    lang = s["language"]
    sid = session.get("sid")
    if sid:
        sessions[sid] = create_fresh_session()
        sessions[sid]["language"] = lang
    logger.info("Session ended")
    return jsonify({"success": True, "message": msg})


@app.route("/api/tts", methods=["POST"])
def tts_endpoint():
    """Generate TTS audio using gTTS (Google Text-to-Speech)."""
    text = request.json.get("text", "") if request.json else ""
    lang = request.json.get("language", "English") if request.json else "English"

    text = sanitize_input(text, max_length=1000)
    if not text:
        return jsonify({"error": "Empty text"}), 400

    tts_code = LANGUAGES.get(lang, LANGUAGES["English"])["tts_code"]

    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang=tts_code, slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return send_file(buf, mimetype="audio/mpeg")
    except Exception as e:
        logger.error("TTS error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/translations")
def get_translations():
    """Return UI translations for the requested language."""
    s, _ = get_session()
    lang = request.args.get("language", s["language"])
    # Validate language
    if lang not in UI_TEXT:
        lang = "English"
    texts = UI_TEXT.get(lang, UI_TEXT["English"])
    return jsonify(texts)


# ═══════════════════════════════════════════════════════════
# Run
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")
