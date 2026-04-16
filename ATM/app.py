"""
╔══════════════════════════════════════════════════════════════╗
║  Smart ATM Chatbot — Flask Backend + API                    ║
║  Serves the frontend and provides REST API endpoints        ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import io
import uuid
import time
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
import random
import re

from flask import Flask, render_template, request, jsonify, session, send_file
from dotenv import load_dotenv

load_dotenv()

# ── App Setup ──
app = Flask(__name__,
            template_folder="templates",
            static_folder="static")
app.secret_key = os.urandom(24)

BASE_DIR = Path(__file__).parent

# ═══════════════════════════════════════════════════════════
# In-Memory Session Store
# ═══════════════════════════════════════════════════════════
sessions = {}

DEFAULT_PIN = "1234"
DEFAULT_PIN_HASH = hashlib.sha256(DEFAULT_PIN.encode()).hexdigest()
DAILY_LIMIT = 20000
PER_TX_LIMIT = 10000
INITIAL_BALANCE = 25000
MAX_PIN_ATTEMPTS = 3
LOCKOUT_SECONDS = 30
SESSION_TIMEOUT = 120

# ── Load translations ──
from src.translations import LANGUAGES, UI_TEXT, get_text

# ── Load knowledge base ──
KB_PATH = BASE_DIR / "data" / "banking_knowledge.json"
KNOWLEDGE_BASE = []
if KB_PATH.exists():
    with open(KB_PATH, "r", encoding="utf-8") as f:
        KNOWLEDGE_BASE = json.load(f)


def get_session():
    """Get or create a session."""
    sid = session.get("sid")
    if not sid or sid not in sessions:
        sid = str(uuid.uuid4())
        session["sid"] = sid
        sessions[sid] = create_fresh_session()
    s = sessions[sid]
    # Check timeout
    if s["card_inserted"] and s["pin_verified"]:
        if time.time() - s["last_activity"] > SESSION_TIMEOUT:
            lang = s["language"]
            sessions[sid] = create_fresh_session()
            sessions[sid]["language"] = lang
            return sessions[sid], True  # timed out
    s["last_activity"] = time.time()
    return s, False


def create_fresh_session():
    """Create a new empty session state."""
    tx_types = [
        ("Credit", "Salary Credited", 2000, 50000),
        ("Debit", "ATM Withdrawal", 500, 10000),
        ("Credit", "UPI Transfer Received", 100, 5000),
        ("Debit", "Online Purchase", 200, 15000),
        ("Debit", "Bill Payment", 100, 5000),
        ("Credit", "Refund", 50, 2000),
    ]
    history = []
    bal = INITIAL_BALANCE
    now = datetime.now()
    for i in range(10):
        tt, desc, mn, mx = random.choice(tx_types)
        amt = random.randrange(mn, mx, 100)
        if tt == "Credit":
            bal += amt
        else:
            if bal >= amt:
                bal -= amt
            else:
                continue
        history.append({
            "date": (now - timedelta(days=i, hours=random.randint(1, 23))).strftime("%d-%b-%Y %H:%M"),
            "type": tt, "description": desc, "amount": amt, "balance": bal
        })
    history.reverse()

    return {
        "card_inserted": False,
        "pin_verified": False,
        "pin_attempts": 0,
        "pin_locked_until": 0,
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


def format_currency(amount):
    """Format amount in Indian currency style."""
    s = str(int(amount))
    if len(s) <= 3:
        return f"₹{s}"
    last_three = s[-3:]
    remaining = s[:-3]
    groups = []
    while len(remaining) > 2:
        groups.insert(0, remaining[-2:])
        remaining = remaining[:-2]
    if remaining:
        groups.insert(0, remaining)
    return f"₹{','.join(groups)},{last_three}"


def t(s, key, **kwargs):
    """Get translated text."""
    return get_text(s["language"], key, **kwargs)


# ═══════════════════════════════════════════════════════════
# NLP — Intent & Entity Extraction (inline for speed)
# ═══════════════════════════════════════════════════════════
INTENT_KW = {
    "withdraw": ["withdraw", "withdrawal", "cash", "take out", "want money", "need money", "get money", "give me",
                  "निकासी", "निकालना", "पैसे", "नकद", "रुपये", "रुपया", "चाहिए",
                  "ઉપાડ", "ઉપાડવા", "રૂપિયા", "પૈસા", "રોકડ", "જોઈએ",
                  "काढणे", "काढा", "रोख", "रक्कम", "हवे",
                  "எடுக்க", "பணம்", "ரூபாய்",
                  "విత్‌డ్రా", "డబ్బు", "రూపాయలు", "నగదు", "కావాలి",
                  "তোলা", "টাকা", "নগদ", "চাই"],
    "balance": ["balance", "check balance", "how much", "remaining", "available",
                "शेष", "बैलेंस", "कितना", "खाता",
                "બેલેન્સ", "બાકી", "કેટલા",
                "शिल्लक", "बॅलन्स", "किती",
                "இருப்பு", "எவ்வளவு",
                "బ్యాలెన్స్", "ఎంత",
                "ব্যালেন্স", "কত"],
    "mini_statement": ["mini statement", "statement", "transaction history", "recent transactions", "history",
                       "मिनी स्टेटमेंट", "स्टेटमेंट", "लेन-देन",
                       "મિની સ્ટેટમેન્ટ", "વ્યવહાર",
                       "मिनी स्टेटमेंट", "व्यवहार",
                       "மினி அறிக்கை", "பரிவர்த்தனை",
                       "మినీ స్టేట్‌మెంట్", "లావాదేవీ",
                       "মিনি স্টেটমেন্ট", "লেনদেন"],
    "greeting": ["hello", "hi", "hey", "good morning", "namaste",
                 "नमस्ते", "हेलो", "નમસ્તે", "হ্যালো", "வணக்கம்", "నమస్కారం", "नमस्कार"],
    "goodbye": ["bye", "goodbye", "exit", "quit", "end", "done", "thank", "close",
                "अलविदा", "धन्यवाद", "આવજો", "আভার", "निरोप", "நன்றி", "ధన్యవాదాలు", "বিদায়"],
}

NUMERAL_MAPS = [
    str.maketrans("०१२३४५६७८९", "0123456789"),
    str.maketrans("૦૧૨૩૪૫૬૭૮૯", "0123456789"),
    str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789"),
    str.maketrans("௦௧௨௩௪௫௬௭௮௯", "0123456789"),
    str.maketrans("౦౧౨౩౪౫౬౭౮౯", "0123456789"),
]


def extract_amount(text):
    for m in NUMERAL_MAPS:
        text = text.translate(m)
    patterns = [r"₹\s*([\d,]+)", r"rs\.?\s*([\d,]+)", r"([\d,]+)\s*(?:₹|rs|rupee|रुपय|રૂપિયા|ரூபாய்|రూపాయ|টাকা)",
                r"\b(\d{3,})\b"]
    for p in patterns:
        match = re.search(p, text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1).replace(",", ""))
            except ValueError:
                continue
    nums = re.findall(r"\b(\d+)\b", text)
    for n in nums:
        val = int(n)
        if 100 <= val <= 100000:
            return val
    return None


def classify_intent(text, lang="English"):
    text_lower = text.lower().strip()
    scores = {}
    for intent, kws in INTENT_KW.items():
        sc = sum(2 for kw in kws if kw.lower() in text_lower)
        if sc > 0:
            scores[intent] = sc
    amount = extract_amount(text)
    if scores:
        best = max(scores, key=scores.get)
        conf = min(1.0, scores[best] / 4.0)
        if amount and best not in ("withdraw",):
            best = "withdraw"
        return {"intent": best, "confidence": conf, "amount": amount}
    if amount:
        return {"intent": "withdraw", "confidence": 0.4, "amount": amount}
    return {"intent": "unknown", "confidence": 0, "amount": amount}


# ═══════════════════════════════════════════════════════════
# RAG — Keyword search over knowledge base
# ═══════════════════════════════════════════════════════════
STOP_WORDS = {"the", "a", "an", "is", "are", "was", "were", "be", "do", "does", "did",
              "can", "could", "will", "would", "should", "i", "me", "my", "we", "you",
              "your", "it", "they", "this", "that", "what", "which", "how", "when",
              "where", "why", "from", "to", "in", "on", "at", "for", "of", "with",
              "and", "or", "not", "no", "if", "but", "so", "as", "by", "up"}


def search_knowledge(query, top_k=3):
    query_words = set(re.findall(r'\w+', query.lower())) - STOP_WORDS
    results = []
    for entry in KNOWLEDGE_BASE:
        entry_text = f"{entry['question']} {entry['answer']} {entry['category']}".lower()
        entry_words = set(re.findall(r'\w+', entry_text))
        common = query_words & entry_words
        score = len(common) * 3
        for w in query_words:
            if w in entry['question'].lower():
                score += 2
            if w in entry['category'].lower():
                score += 1
        if score > 0:
            results.append((score, entry))
    results.sort(key=lambda x: x[0], reverse=True)
    return [e for _, e in results[:top_k]]


# ═══════════════════════════════════════════════════════════
# API Routes
# ═══════════════════════════════════════════════════════════
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/session-status")
def session_status():
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
    s, _ = get_session()
    s["card_inserted"] = True
    s["pin_verified"] = False
    s["pin_attempts"] = 0
    s["pin_locked_until"] = 0
    s["last_activity"] = time.time()
    welcome = t(s, "welcome")
    s["chat_history"].append({"role": "bot", "content": welcome, "time": datetime.now().strftime("%H:%M")})
    return jsonify({"success": True, "message": welcome})


@app.route("/api/set-language", methods=["POST"])
def set_language():
    s, _ = get_session()
    lang = request.json.get("language", "English")
    if lang in LANGUAGES:
        s["language"] = lang
    return jsonify({"success": True, "language": s["language"]})


@app.route("/api/validate-pin", methods=["POST"])
def validate_pin():
    s, _ = get_session()
    pin = request.json.get("pin", "")

    if s["pin_locked_until"] > time.time():
        remaining = int(s["pin_locked_until"] - time.time())
        return jsonify({"success": False, "locked": True, "remaining": remaining,
                        "message": t(s, "pin_locked")})

    if s["pin_locked_until"] > 0 and s["pin_locked_until"] <= time.time():
        s["pin_locked_until"] = 0
        s["pin_attempts"] = 0

    if not pin or len(pin) != 4 or not pin.isdigit():
        return jsonify({"success": False, "message": "Invalid PIN format"})

    pin_hash = hashlib.sha256(pin.encode()).hexdigest()
    if pin_hash == DEFAULT_PIN_HASH:
        s["pin_verified"] = True
        s["pin_attempts"] = 0
        s["last_activity"] = time.time()
        msg = t(s, "pin_correct")
        # Execute pending action
        result = {"success": True, "message": msg, "authenticated": True}
        if s.get("pending_action"):
            tx_result = execute_action(s, s["pending_action"], s.get("pending_amount"))
            result["action_result"] = tx_result
            s["pending_action"] = None
            s["pending_amount"] = None
        return jsonify(result)
    else:
        s["pin_attempts"] += 1
        if s["pin_attempts"] >= MAX_PIN_ATTEMPTS:
            s["pin_locked_until"] = time.time() + LOCKOUT_SECONDS
            return jsonify({"success": False, "locked": True, "remaining": LOCKOUT_SECONDS,
                            "message": t(s, "pin_locked")})
        remaining = MAX_PIN_ATTEMPTS - s["pin_attempts"]
        return jsonify({"success": False, "locked": False,
                        "message": f"{t(s, 'pin_incorrect')} {t(s, 'attempts_remaining', n=remaining)}"})


@app.route("/api/process", methods=["POST"])
def process_input():
    s, timed_out = get_session()
    if timed_out:
        return jsonify({"type": "timeout", "message": t(s, "session_timeout")})

    text = request.json.get("text", "").strip()
    if not text:
        return jsonify({"type": "error", "message": "Empty input"})

    s["last_activity"] = time.time()
    result = classify_intent(text, s["language"])
    intent = result["intent"]
    amount = result["amount"]

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
            return jsonify({"type": "need_pin", "message": t(s, "enter_pin"), "intent": intent})
        return jsonify(execute_action(s, intent, amount))

    # FAQ / Unknown → knowledge search
    results = search_knowledge(text)
    if results:
        answer = results[0]["answer"]
        return jsonify({"type": "faq", "message": answer})

    return jsonify({"type": "help", "message": t(s, "ask_anything")})


def execute_action(s, intent, amount=None):
    """Execute a banking action."""
    if intent == "balance":
        msg = t(s, "balance_result", balance=format_currency(s["balance"]))
        return {"type": "balance", "message": msg, "balance": s["balance"],
                "formatted_balance": format_currency(s["balance"])}

    elif intent == "mini_statement":
        txns = s["transaction_history"][-5:]
        msg = t(s, "mini_statement")
        return {"type": "mini_statement", "message": msg, "transactions": txns,
                "balance": s["balance"], "formatted_balance": format_currency(s["balance"]),
                "card_number": s["card_number"]}

    elif intent == "withdraw":
        if amount is None:
            return {"type": "need_amount", "message": t(s, "enter_amount")}

        if amount <= 0 or amount % 100 != 0:
            return {"type": "error", "message": t(s, "invalid_amount")}
        if amount > PER_TX_LIMIT:
            return {"type": "error", "message": t(s, "exceed_limit", limit=format_currency(PER_TX_LIMIT))}

        today = datetime.now().date()
        if s.get("last_withdrawal_date") != str(today):
            s["daily_withdrawn"] = 0
        if s["daily_withdrawn"] + amount > DAILY_LIMIT:
            rem = DAILY_LIMIT - s["daily_withdrawn"]
            return {"type": "error", "message": t(s, "exceed_limit", limit=format_currency(rem))}
        if amount > s["balance"]:
            return {"type": "error", "message": t(s, "insufficient_funds", balance=format_currency(s["balance"]))}

        # Process withdrawal
        s["balance"] -= amount
        s["daily_withdrawn"] += amount
        s["last_withdrawal_date"] = str(today)
        ref = f"ATM{random.randint(100000, 999999)}"
        tx = {"date": datetime.now().strftime("%d-%b-%Y %H:%M"), "type": "Debit",
              "description": "ATM Cash Withdrawal", "amount": amount, "balance": s["balance"]}
        s["transaction_history"].append(tx)

        receipt = {
            "card_number": s["card_number"],
            "date_time": datetime.now().strftime("%d-%b-%Y %H:%M:%S"),
            "transaction_type": "Cash Withdrawal",
            "amount": amount, "formatted_amount": format_currency(amount),
            "available_balance": s["balance"],
            "formatted_balance": format_currency(s["balance"]),
            "reference_no": ref,
        }
        msg = t(s, "withdraw_success", amount=format_currency(amount))
        return {"type": "withdraw_success", "message": msg, "receipt": receipt,
                "collect_msg": t(s, "collect_cash")}

    return {"type": "error", "message": "Unknown action"}


@app.route("/api/withdraw", methods=["POST"])
def api_withdraw():
    s, _ = get_session()
    if not s["pin_verified"]:
        return jsonify({"type": "need_pin", "message": t(s, "enter_pin")})
    amount = request.json.get("amount", 0)
    result = execute_action(s, "withdraw", int(amount))
    return jsonify(result)


@app.route("/api/end-session", methods=["POST"])
def end_session_api():
    s, _ = get_session()
    msg = t(s, "goodbye")
    lang = s["language"]
    sid = session.get("sid")
    if sid:
        sessions[sid] = create_fresh_session()
        sessions[sid]["language"] = lang
    return jsonify({"success": True, "message": msg})


@app.route("/api/tts", methods=["POST"])
def tts_endpoint():
    """Generate TTS audio using gTTS."""
    text = request.json.get("text", "")
    lang = request.json.get("language", "English")
    tts_code = LANGUAGES.get(lang, LANGUAGES["English"])["tts_code"]

    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang=tts_code, slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return send_file(buf, mimetype="audio/mpeg")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/translations")
def get_translations():
    s, _ = get_session()
    lang = request.args.get("language", s["language"])
    texts = UI_TEXT.get(lang, UI_TEXT["English"])
    return jsonify(texts)


# ═══════════════════════════════════════════════════════════
# Run
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")
