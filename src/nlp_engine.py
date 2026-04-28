"""
NLP Engine — Intent classification and entity extraction.
Supports multilingual input with keyword-based matching + regex.
Supports 20 Indian languages.
"""

import re


# ─────────────────────────────────────────────────────────────
# Language code map (language name → short code)
# ─────────────────────────────────────────────────────────────
LANG_CODES = {
    "English": "en", "Hindi": "hi", "Gujarati": "gu", "Marathi": "mr",
    "Tamil": "ta", "Telugu": "te", "Bengali": "bn", "Punjabi": "pa",
    "Kashmiri": "ks", "Ladakhi": "lad", "Manipuri": "mni", "Ao": "ao",
    "Nissi": "nsi", "Khasi": "kha", "Odia": "or", "Assamese": "as",
    "Nepali": "ne", "Malayalam": "ml", "Kannada": "kn", "Konkani": "kok",
}

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
        "pa": ["ਪੈਸੇ", "ਕਢਵਾਓ", "ਨਕਦ", "ਰੁਪਏ", "ਕੱਢੋ", "ਚਾਹੀਦਾ"],
        "ml": ["പിൻവലിക്കുക", "പണം", "രൂപ", "നഗദ്", "എടുക്കുക"],
        "kn": ["ಹಿಂಪಡೆಯಿರಿ", "ಹಣ", "ರೂಪಾಯಿ", "ನಗದು", "ತೆಗೆಯಿರಿ", "ಬೇಕು"],
        "or": ["ଉଠାନ୍ତୁ", "ଟଙ୍କା", "ରୁପିଆ", "ନଗଦ", "କାଢନ୍ତୁ"],
        "as": ["উলিয়াওক", "টকা", "নগদ", "টানক"],
        "ne": ["निकाल्नुहोस्", "पैसा", "रुपैयाँ", "नगद", "चाहिन्छ"],
        "kok": ["काडात", "पयशे", "रुपया", "नगद"],
        "ks": ["رقم", "کھسِو", "پیسہ", "نقد"],
        "mni": ["লৌথোকউ", "শেনফম", "পৈসা"],
    },
    "balance": {
        "en": ["balance", "check balance", "account balance", "how much", "remaining", "available", "kitna"],
        "hi": ["शेष", "बैलेंस", "बचत", "कितना", "जमा", "खाता", "बाकी", "शेष राशि"],
        "gu": ["બેલેન્સ", "બાકી", "જમા", "કેટલા", "ખાતું", "શેષ"],
        "mr": ["शिल्लक", "बॅलन्स", "किती", "खाते", "जमा", "बाकी"],
        "ta": ["இருப்பு", "பேலன்ஸ்", "எவ்வளவு", "கணக்கு"],
        "te": ["బ్యాలెన్స్", "ఎంత", "ఖాతా", "మిగిలింది"],
        "bn": ["ব্যালেন্স", "কত", "জমা", "অ্যাকাউন্ট", "বাকি"],
        "pa": ["ਬੈਲੰਸ", "ਕਿੰਨਾ", "ਖਾਤਾ", "ਬਾਕੀ", "ਜਮ੍ਹਾਂ"],
        "ml": ["ബാലൻസ്", "എത്ര", "അക്കൗണ്ട്", "ശേഷിക്കുന്ന"],
        "kn": ["ಬ್ಯಾಲೆನ್ಸ್", "ಎಷ್ಟು", "ಖಾತೆ", "ಉಳಿದಿದೆ"],
        "or": ["ବ୍ୟାଲେନ୍ସ", "କେତେ", "ଖାତା", "ବାକି"],
        "as": ["বেলেঞ্চ", "কিমান", "একাউণ্ট", "বাকী"],
        "ne": ["ब्यालेन्स", "कति", "खाता", "बाँकी"],
        "kok": ["बॅलन्स", "किती", "खातो", "बाकी"],
        "ks": ["بیلنس", "کتھ", "اکاؤنٹ"],
        "mni": ["ব্যালেন্স", "কয়দা", "একাউন্ট"],
    },
    "mini_statement": {
        "en": ["mini statement", "statement", "transaction history", "recent transactions", "last transactions", "history"],
        "hi": ["मिनी स्टेटमेंट", "स्टेटमेंट", "लेन-देन", "हाल के लेन-देन", "विवरण", "इतिहास"],
        "gu": ["મિની સ્ટેટમેન્ટ", "સ્ટેટમેન્ટ", "વ્યવહાર", "ઇતિહાસ", "વિગત"],
        "mr": ["मिनी स्टेटमेंट", "स्टेटमेंट", "व्यवहार", "इतिहास", "हालचाल"],
        "ta": ["மினி அறிக்கை", "அறிக்கை", "பரிவர்த்தனை", "வரலாறு"],
        "te": ["మినీ స్టేట్‌మెంట్", "స్టేట్‌మెంట్", "లావాదేవీ", "చరిత్ర"],
        "bn": ["মিনি স্টেটমেন্ট", "স্টেটমেন্ট", "লেনদেন", "ইতিহাস"],
        "pa": ["ਮਿਨੀ ਸਟੇਟਮੈਂਟ", "ਸਟੇਟਮੈਂਟ", "ਲੈਣ-ਦੇਣ", "ਇਤਿਹਾਸ"],
        "ml": ["മിനി സ്റ്റേറ്റ്‌മെന്റ്", "ഇടപാട്", "ചരിത്രം"],
        "kn": ["ಮಿನಿ ಸ್ಟೇಟ್‌ಮೆಂಟ್", "ವಹಿವಾಟು", "ಇತಿಹಾಸ"],
        "or": ["ମିନି ଷ୍ଟେଟମେଣ୍ଟ", "ଲେନଦେନ", "ଇତିହାସ"],
        "as": ["মিনি ষ্টেটমেণ্ট", "লেনদেন", "ইতিহাস"],
        "ne": ["मिनी स्टेटमेन्ट", "कारोबार", "इतिहास"],
        "kok": ["मिनी स्टेटमेंट", "व्यवहार", "इतिहास"],
    },
    "help": {
        "en": ["help", "assist", "support", "what can you do", "options", "services", "guide", "how to", "information", "info"],
        "hi": ["मदद", "सहायता", "क्या कर सकते", "विकल्प", "सेवाएं", "जानकारी", "कैसे"],
        "gu": ["મદદ", "સહાય", "શું કરી શકો", "વિકલ્પ", "સેવાઓ", "માહિતી", "કેવી રીતે"],
        "mr": ["मदत", "सहाय्य", "काय करता येते", "पर्याय", "सेवा", "माहिती", "कसे"],
        "ta": ["உதவி", "என்ன செய்ய முடியும்", "விருப்பங்கள்", "சேவைகள்", "தகவல்"],
        "te": ["సహాయం", "ఏమి చేయగలరు", "ఎంపికలు", "సేవలు", "సమాచారం"],
        "bn": ["সাহায্য", "কী করতে পারেন", "বিকল্প", "সেবা", "তথ্য"],
        "pa": ["ਮਦਦ", "ਸਹਾਇਤਾ", "ਸੇਵਾਵਾਂ", "ਜਾਣਕਾਰੀ", "ਕਿਵੇਂ"],
        "ml": ["സഹായം", "സേവനങ്ങൾ", "വിവരം", "എങ്ങനെ"],
        "kn": ["ಸಹಾಯ", "ಸೇವೆಗಳು", "ಮಾಹಿತಿ", "ಹೇಗೆ"],
        "or": ["ସାହାଯ୍ୟ", "ସେବା", "ସୂଚନା", "କେମିତି"],
        "as": ["সহায়", "সেৱা", "তথ্য", "কেনেকৈ"],
        "ne": ["मद्दत", "सेवा", "जानकारी", "कसरी"],
        "kok": ["मजत", "सेवा", "म्हायती", "कशें"],
    },
    "greeting": {
        "en": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "namaste"],
        "hi": ["नमस्ते", "नमस्कार", "हेलो", "हाय", "शुभ प्रभात"],
        "gu": ["નમસ્તે", "નમસ્કાર", "હેલો", "કેમ છો", "શુભ સવાર"],
        "mr": ["नमस्कार", "हेलो", "नमस्ते", "शुभ सकाळ"],
        "ta": ["வணக்கம்", "நமஸ்காரம்", "ஹலோ"],
        "te": ["నమస్కారం", "హలో", "నమస్తే"],
        "bn": ["নমস্কার", "হ্যালো", "শুভ সকাল"],
        "pa": ["ਸਤ ਸ੍ਰੀ ਅਕਾਲ", "ਨਮਸਤੇ", "ਹੈਲੋ", "ਕਿਦਾਂ"],
        "ml": ["നമസ്കാരം", "ഹലോ", "സുപ്രഭാതം"],
        "kn": ["ನಮಸ್ಕಾರ", "ಹಲೋ", "ಶುಭೋದಯ"],
        "or": ["ନମସ୍କାର", "ହେଲୋ"],
        "as": ["নমস্কাৰ", "হেলো"],
        "ne": ["नमस्कार", "नमस्ते", "हेलो"],
        "kok": ["नमस्कार", "हॅलो"],
        "ks": ["آداب", "السلام علیکم", "ہیلو"],
        "mni": ["খুরুমজরি", "হ্যালো"],
    },
    "goodbye": {
        "en": ["bye", "goodbye", "exit", "quit", "end", "done", "thank you", "thanks", "close"],
        "hi": ["अलविदा", "धन्यवाद", "बंद", "बाय", "खत्म", "समाप्त"],
        "gu": ["આવજો", "આભાર", "ધન્યવાદ", "બંધ", "બાય"],
        "mr": ["निरोप", "धन्यवाद", "बंद", "बाय", "संपवा"],
        "ta": ["பை", "நன்றி", "முடி", "வணக்கம்"],
        "te": ["బై", "ధన్యవాదాలు", "ముగించు", "మూసేయి"],
        "bn": ["বিদায়", "ধন্যবাদ", "বন্ধ", "বাই"],
        "pa": ["ਅਲਵਿਦਾ", "ਧੰਨਵਾਦ", "ਬੰਦ", "ਬਾਏ"],
        "ml": ["വിട", "നന്ദി", "ബൈ"],
        "kn": ["ವಿದಾಯ", "ಧನ್ಯವಾದ", "ಬೈ"],
        "or": ["ବିଦାୟ", "ଧନ୍ୟବାଦ", "ବନ୍ଦ"],
        "as": ["বিদায়", "ধন্যবাদ", "বন্ধ"],
        "ne": ["बिदा", "धन्यवाद", "बन्द"],
        "kok": ["उपकार", "बंद", "बाय"],
        "ks": ["خدا حافظ", "شکریہ"],
        "mni": ["নুংশিরবশিং", "থাগৎচরি"],
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
        "pa": ["ਸੀਮਾ", "ਚਾਰਜ", "ਫੀਸ", "ਨਿਯਮ", "ਕੀ ਹੈ", "ਕਿੰਨਾ", "ਕਿਉਂ", "ਕਦੋਂ", "ਕਾਰਡ", "ਸ਼ਿਕਾਇਤ"],
        "ml": ["പരിധി", "ചാർജ്", "ഫീസ്", "നിയമം", "എന്താണ്", "എത്ര", "എന്തുകൊണ്ട്", "കാർഡ്"],
        "kn": ["ಮಿತಿ", "ಶುಲ್ಕ", "ನಿಯಮ", "ಏನು", "ಎಷ್ಟು", "ಏಕೆ", "ಯಾವಾಗ", "ಕಾರ್ಡ್"],
        "or": ["ସୀମା", "ଚାର୍ଜ", "ନିୟମ", "କ'ଣ", "କେତେ", "କାହିଁକି", "କାର୍ଡ"],
        "as": ["সীমা", "চাৰ্জ", "নিয়ম", "কি", "কিমান", "কিয়", "কাৰ্ড"],
        "ne": ["सीमा", "शुल्क", "नियम", "के हो", "कति", "किन", "कार्ड"],
        "kok": ["मर्यादा", "शुल्क", "नेम", "किते", "कित्या", "कार्ड"],
    },
}

# ─────────────────────────────────────────────────────────────
# Amount extraction patterns
# ─────────────────────────────────────────────────────────────
# Regional numerals → Latin
DEVANAGARI_MAP = str.maketrans("०१२३४५६७८९", "0123456789")
GUJARATI_MAP = str.maketrans("૦૧૨૩૪૫૬૭૮૯", "0123456789")
BENGALI_MAP = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
TAMIL_MAP = str.maketrans("௦௧௨௩௪௫௬௭௮௯", "0123456789")
TELUGU_MAP = str.maketrans("౦౧౨౩౪౫౬౭౮౯", "0123456789")
GURMUKHI_MAP = str.maketrans("੦੧੨੩੪੫੬੭੮੯", "0123456789")
KANNADA_MAP = str.maketrans("೦೧೨೩೪೫೬೭೮೯", "0123456789")
MALAYALAM_MAP = str.maketrans("൦൧൨൩൪൫൬൭൮൯", "0123456789")
ODIA_MAP = str.maketrans("୦୧୨୩୪୫୬୭୮୯", "0123456789")


def _normalize_numerals(text: str) -> str:
    """Convert regional script numerals to Latin digits."""
    for m in [DEVANAGARI_MAP, GUJARATI_MAP, BENGALI_MAP, TAMIL_MAP,
              TELUGU_MAP, GURMUKHI_MAP, KANNADA_MAP, MALAYALAM_MAP, ODIA_MAP]:
        text = text.translate(m)
    return text


def extract_amount(text: str) -> int | None:
    """Extract a monetary amount from text. Handles ₹, Rs, regional numerals."""
    text = _normalize_numerals(text)
    patterns = [
        r"₹\s*([\d,]+)",
        r"rs\.?\s*([\d,]+)",
        r"rupees?\s*([\d,]+)",
        r"([\d,]+)\s*(?:₹|rs\.?|rupees?|रुपये|रुपया|રૂપિયા|ரூபாய்|రూపాయలు|টাকা|ਰੁਪਏ|രൂപ|ರೂಪಾಯಿ|ରୁପିଆ|रुपैयाँ)",
        r"([\d,]+)\s*(?:hundred|हजार|thousand|lakh)",
        r"\b(\d{3,})\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(",", "")
            try:
                return int(amount_str)
            except ValueError:
                continue
    numbers = re.findall(r"\b(\d+)\b", text)
    for num_str in numbers:
        num = int(num_str)
        if 100 <= num <= 100000:
            return num
    return None


def classify_intent(text: str, language: str = "English") -> dict:
    """Classify user intent from text input across 20 languages."""
    text_lower = text.lower().strip()
    lang_code = LANG_CODES.get(language, "en")

    result = {
        "intent": "unknown",
        "confidence": 0.0,
        "entities": {"amount": extract_amount(text)},
        "raw_text": text,
    }

    scores = {}
    for intent, lang_keywords in INTENT_KEYWORDS.items():
        score = 0
        for kw in lang_keywords.get(lang_code, []):
            if kw.lower() in text_lower:
                score += 2
        if lang_code != "en":
            for kw in lang_keywords.get("en", []):
                if kw.lower() in text_lower:
                    score += 1
        # Also check Hindi as secondary fallback for Devanagari-based languages
        if lang_code in ("ne", "kok", "ks", "lad") and lang_code != "hi":
            for kw in lang_keywords.get("hi", []):
                if kw.lower() in text_lower:
                    score += 1
        # Bengali fallback for Assamese/Manipuri
        if lang_code in ("as", "mni") and lang_code != "bn":
            for kw in lang_keywords.get("bn", []):
                if kw.lower() in text_lower:
                    score += 1
        if score > 0:
            scores[intent] = score

    if scores:
        best_intent = max(scores, key=scores.get)
        max_score = scores[best_intent]
        confidence = min(1.0, max_score / 4.0)
        result["intent"] = best_intent
        result["confidence"] = confidence
        if result["entities"]["amount"] and best_intent not in ("withdraw", "faq"):
            if "withdraw" in scores:
                result["intent"] = "withdraw"
            elif result["entities"]["amount"]:
                result["intent"] = "withdraw"
                result["confidence"] = max(0.5, confidence)

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
