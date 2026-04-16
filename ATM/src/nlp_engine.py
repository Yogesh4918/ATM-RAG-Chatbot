"""
NLP Engine — Intent classification and entity extraction.
Supports multilingual input with keyword-based matching + regex.
"""

import re


# ─────────────────────────────────────────────────────────────
# Intent keywords in all supported languages
# ─────────────────────────────────────────────────────────────
INTENT_KEYWORDS = {
    "withdraw": {
        "en": ["withdraw", "withdrawal", "cash", "take out", "want money", "need money", "get money", "give me", "nikalo", "paisa"],
        "hi": ["निकासी", "निकालना", "पैसे", "नकद", "निकालो", "रुपये", "रुपया", "पैसा", "निकालें", "चाहिए"],
        "gu": ["ઉપાડ", "ઉપાડવા", "રૂપિયા", "પૈસા", "રોકડ", "ઉપાડો", "જોઈએ"],
        "mr": ["काढणे", "काढा", "पैसे", "रोख", "रक्कम", "रुपये", "हवे"],
        "ta": ["எடுக்க", "பணம்", "ரூபாய்", "எடு", "நகதை"],
        "te": ["విత్‌డ్రా", "డబ్బు", "రూపాయలు", "నగదు", "తీయండి", "కావాలి"],
        "bn": ["তোলা", "টাকা", "নগদ", "রুপি", "তুলতে", "চাই"],
    },
    "balance": {
        "en": ["balance", "check balance", "account balance", "how much", "remaining", "available", "kitna"],
        "hi": ["शेष", "बैलेंस", "बचत", "कितना", "जमा", "खाता", "बाकी", "शेष राशि"],
        "gu": ["બેલેન્સ", "બાકી", "જમા", "કેટલા", "ખાતું", "શેષ"],
        "mr": ["शिल्लक", "बॅलन्स", "किती", "खाते", "जमा", "बाकी"],
        "ta": ["இருப்பு", "பேலன்ஸ்", "எவ்வளவு", "கணக்கு"],
        "te": ["బ్యాలెన్స్", "ఎంత", "ఖాతా", "మిగిలింది"],
        "bn": ["ব্যালেন্স", "কত", "জমা", "অ্যাকাউন্ট", "বাকি"],
    },
    "mini_statement": {
        "en": ["mini statement", "statement", "transaction history", "recent transactions", "last transactions", "history"],
        "hi": ["मिनी स्टेटमेंट", "स्टेटमेंट", "लेन-देन", "हाल के लेन-देन", "विवरण", "इतिहास"],
        "gu": ["મિની સ્ટેટમેન્ટ", "સ્ટેટમેન્ટ", "વ્યવહાર", "ઇતિહાસ", "વિગત"],
        "mr": ["मिनी स्टेटमेंट", "स्टेटमेंट", "व्यवहार", "इतिहास", "हालचाल"],
        "ta": ["மினி அறிக்கை", "அறிக்கை", "பரிவர்த்தனை", "வரலாறு"],
        "te": ["మినీ స్టేట్‌మెంట్", "స్టేట్‌మెంట్", "లావాదేవీ", "చరిత్ర"],
        "bn": ["মিনি স্টেটমেন্ট", "স্টেটমেন্ট", "লেনদেন", "ইতিহাস"],
    },
    "help": {
        "en": ["help", "assist", "support", "what can you do", "options", "services", "guide", "how to", "information", "info"],
        "hi": ["मदद", "सहायता", "क्या कर सकते", "विकल्प", "सेवाएं", "जानकारी", "कैसे"],
        "gu": ["મદદ", "સહાય", "શું કરી શકો", "વિકલ્પ", "સેવાઓ", "માહિતી", "કેવી રીતે"],
        "mr": ["मदत", "सहाय्य", "काय करता येते", "पर्याय", "सेवा", "माहिती", "कसे"],
        "ta": ["உதவி", "என்ன செய்ய முடியும்", "விருப்பங்கள்", "சேவைகள்", "தகவல்"],
        "te": ["సహాయం", "ఏమి చేయగలరు", "ఎంపికలు", "సేవలు", "సమాచారం"],
        "bn": ["সাহায্য", "কী করতে পারেন", "বিকল্প", "সেবা", "তথ্য"],
    },
    "greeting": {
        "en": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "namaste"],
        "hi": ["नमस्ते", "नमस्कार", "हेलो", "हाय", "शुभ प्रभात"],
        "gu": ["નમસ્તે", "નમસ્કાર", "હેલો", "કેમ છો", "શુભ સવાર"],
        "mr": ["नमस्कार", "हेलो", "नमस्ते", "शुभ सकाळ"],
        "ta": ["வணக்கம்", "நமஸ்காரம்", "ஹலோ"],
        "te": ["నమస్కారం", "హలో", "నమస్తే"],
        "bn": ["নমস্কার", "হ্যালো", "শুভ সকাল"],
    },
    "goodbye": {
        "en": ["bye", "goodbye", "exit", "quit", "end", "done", "thank you", "thanks", "close"],
        "hi": ["अलविदा", "धन्यवाद", "बंद", "बाय", "खत्म", "समाप्त"],
        "gu": ["આવજો", "આભાર", "ધન્યવાદ", "બંધ", "બાય"],
        "mr": ["निरोप", "धन्यवाद", "बंद", "बाय", "संपवा"],
        "ta": ["பை", "நன்றி", "முடி", "வணக்கம்"],
        "te": ["బై", "ధన్యవాదాలు", "ముగించు", "మూసేయి"],
        "bn": ["বিদায়", "ধন্যবাদ", "বন্ধ", "বাই"],
    },
    "faq": {
        "en": ["limit", "charge", "fee", "rule", "policy", "what is", "how much", "why", "when", "where",
               "maximum", "minimum", "card", "lost", "stolen", "blocked", "stuck", "failed", "refund",
               "complaint", "safety", "fraud", "deposit", "transfer"],
        "hi": ["सीमा", "शुल्क", "नियम", "नीति", "क्या है", "कितना", "क्यों", "कब", "कहाँ",
               "अधिकतम", "न्यूनतम", "कार्ड", "खोया", "चोरी", "ब्लॉक", "अटका", "विफल", "वापसी", "शिकायत"],
        "gu": ["મર્યાદા", "ચાર્જ", "ફી", "નિયમ", "નીતિ", "શું છે", "કેટલું", "કેમ", "ક્યારે",
               "મહત્તમ", "ન્યૂનતમ", "કાર્ડ", "ખોવાયેલ", "ચોરી", "બ્લોક", "અટવાયેલ"],
        "mr": ["मर्यादा", "शुल्क", "फी", "नियम", "धोरण", "काय आहे", "किती", "का", "कधी",
               "कमाल", "किमान", "कार्ड", "हरवले", "चोरी", "ब्लॉक"],
        "ta": ["வரம்பு", "கட்டணம்", "விதி", "கொள்கை", "என்ன", "எவ்வளவு", "ஏன்", "எப்போது",
               "அதிகபட்சம்", "குறைந்தபட்சம்", "அட்டை", "தொலைந்த"],
        "te": ["పరిమితి", "ఛార్జీ", "ఫీజు", "నియమం", "విధానం", "ఏమిటి", "ఎంత", "ఎందుకు",
               "గరిష్ఠం", "కనిష్ఠం", "కార్డ్", "పోయింది"],
        "bn": ["সীমা", "চার্জ", "ফি", "নিয়ম", "নীতি", "কি", "কত", "কেন", "কখন",
               "সর্বোচ্চ", "সর্বনিম্ন", "কার্ড", "হারিয়ে", "চুরি", "ব্লক"],
    },
}

# ─────────────────────────────────────────────────────────────
# Amount extraction patterns
# ─────────────────────────────────────────────────────────────
# Devanagari numerals → Latin
DEVANAGARI_MAP = str.maketrans("०१२३४५६७८९", "0123456789")
# Gujarati numerals → Latin
GUJARATI_MAP = str.maketrans("૦૧૨૩૪૫૬૭૮૯", "0123456789")
# Bengali numerals → Latin
BENGALI_MAP = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
# Tamil numerals → Latin
TAMIL_MAP = str.maketrans("௦௧௨௩௪௫௬௭௮௯", "0123456789")
# Telugu numerals → Latin
TELUGU_MAP = str.maketrans("౦౧౨౩౪౫౬౭౮౯", "0123456789")


def _normalize_numerals(text: str) -> str:
    """Convert regional script numerals to Latin digits."""
    text = text.translate(DEVANAGARI_MAP)
    text = text.translate(GUJARATI_MAP)
    text = text.translate(BENGALI_MAP)
    text = text.translate(TAMIL_MAP)
    text = text.translate(TELUGU_MAP)
    return text


def extract_amount(text: str) -> int | None:
    """
    Extract a monetary amount from the text.
    Handles: "500", "₹500", "500 rupees", "Rs 500", regional numerals, etc.
    """
    text = _normalize_numerals(text)

    # Pattern: match numbers (possibly with commas) near currency indicators
    patterns = [
        r"₹\s*([\d,]+)",
        r"rs\.?\s*([\d,]+)",
        r"rupees?\s*([\d,]+)",
        r"([\d,]+)\s*(?:₹|rs\.?|rupees?|रुपये|रुपया|રૂપિયા|रुपये|ரூபாய்|రూపాయలు|টাকা|रुपए)",
        r"([\d,]+)\s*(?:hundred|हजार|thousand|lakh)",
        r"\b(\d{3,})\b",  # Any number with 3+ digits, likely an amount
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(",", "")
            try:
                return int(amount_str)
            except ValueError:
                continue

    # Fallback: find any standalone number
    numbers = re.findall(r"\b(\d+)\b", text)
    for num_str in numbers:
        num = int(num_str)
        if 100 <= num <= 100000:  # Reasonable ATM amount
            return num

    return None


def classify_intent(text: str, language: str = "English") -> dict:
    """
    Classify user intent from text input.
    Returns: {
        "intent": str,          # e.g., "withdraw", "balance", "faq"
        "confidence": float,    # 0.0 to 1.0
        "entities": {           # extracted entities
            "amount": int | None
        },
        "raw_text": str
    }
    """
    text_lower = text.lower().strip()
    lang_code = {
        "English": "en", "Hindi": "hi", "Gujarati": "gu",
        "Marathi": "mr", "Tamil": "ta", "Telugu": "te", "Bengali": "bn"
    }.get(language, "en")

    result = {
        "intent": "unknown",
        "confidence": 0.0,
        "entities": {"amount": extract_amount(text)},
        "raw_text": text,
    }

    # Score each intent
    scores = {}
    for intent, lang_keywords in INTENT_KEYWORDS.items():
        score = 0
        # Check current language keywords
        for kw in lang_keywords.get(lang_code, []):
            if kw.lower() in text_lower:
                score += 2  # Higher weight for current language match

        # Also check English keywords as fallback
        if lang_code != "en":
            for kw in lang_keywords.get("en", []):
                if kw.lower() in text_lower:
                    score += 1

        if score > 0:
            scores[intent] = score

    if scores:
        best_intent = max(scores, key=scores.get)
        max_score = scores[best_intent]
        # Normalize confidence (cap at 1.0)
        confidence = min(1.0, max_score / 4.0)

        result["intent"] = best_intent
        result["confidence"] = confidence

        # If amount is found and intent is not withdraw, prefer withdraw
        if result["entities"]["amount"] and best_intent not in ("withdraw", "faq"):
            if "withdraw" in scores:
                result["intent"] = "withdraw"
            elif result["entities"]["amount"]:
                # If an amount is mentioned, likely a withdrawal
                result["intent"] = "withdraw"
                result["confidence"] = max(0.5, confidence)

    # If we have an amount but no clear intent, assume withdrawal
    if result["intent"] == "unknown" and result["entities"]["amount"]:
        result["intent"] = "withdraw"
        result["confidence"] = 0.4

    return result


def needs_pin_verification(intent: str) -> bool:
    """Check if the given intent requires PIN verification."""
    return intent in ("withdraw", "balance", "mini_statement", "pin_change")


def is_rag_query(intent_result: dict) -> bool:
    """Determine if the query should be routed to the RAG pipeline."""
    return (
        intent_result["intent"] in ("faq", "help", "unknown")
        or intent_result["confidence"] < 0.3
    )
