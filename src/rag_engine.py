"""
RAG Engine — Retrieval-Augmented Generation pipeline.
Uses Google Gemini for AI-powered responses with knowledge base context.
Falls back to keyword-based search when Gemini is unavailable.
"""

import json
import os
import re
import logging
from pathlib import Path
from typing import Optional
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Data paths
# ─────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_FILE = DATA_DIR / "banking_knowledge.json"

# ─────────────────────────────────────────────────────────────
# Language prompts for Gemini responses
# ─────────────────────────────────────────────────────────────
LANGUAGE_INSTRUCTIONS = {
    "English": "Respond in English.",
    "Hindi": "कृपया हिंदी में उत्तर दें। Respond in Hindi language.",
    "Gujarati": "કૃપા કરીને ગુજરાતીમાં જવાબ આપો. Respond in Gujarati language.",
    "Marathi": "कृपया मराठीत उत्तर द्या. Respond in Marathi language.",
    "Tamil": "தமிழில் பதிலளிக்கவும். Respond in Tamil language.",
    "Telugu": "దయచేసి తెలుగులో సమాధానం ఇవ్వండి. Respond in Telugu language.",
    "Bengali": "অনুগ্রহ করে বাংলায় উত্তর দিন. Respond in Bengali language.",
    "Punjabi": "ਕਿਰਪਾ ਕਰਕੇ ਪੰਜਾਬੀ ਵਿੱਚ ਜਵਾਬ ਦਿਓ. Respond in Punjabi language.",
    "Kashmiri": "Respond in Kashmiri language using Devanagari or Nastaliq script.",
    "Ladakhi": "Respond in simple Hindi. The user speaks Ladakhi.",
    "Manipuri": "Respond in Manipuri (Meitei) language using Bengali script.",
    "Ao": "Respond in simple English. The user speaks Ao Naga language.",
    "Nissi": "Respond in simple English. The user speaks Nissi/Nyishi language.",
    "Khasi": "Respond in simple English. The user speaks Khasi language.",
    "Odia": "ଦୟାକରି ଓଡ଼ିଆରେ ଉତ୍ତର ଦିଅନ୍ତୁ. Respond in Odia language.",
    "Assamese": "অনুগ্ৰহ কৰি অসমীয়াত উত্তৰ দিয়ক. Respond in Assamese language.",
    "Nepali": "कृपया नेपालीमा जवाफ दिनुहोस्. Respond in Nepali language.",
    "Malayalam": "ദയവായി മലയാളത്തിൽ മറുപടി നൽകുക. Respond in Malayalam language.",
    "Kannada": "ದಯವಿಟ್ಟು ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರಿಸಿ. Respond in Kannada language.",
    "Konkani": "कृपया कोंकणीत जाप दिवची. Respond in Konkani language.",
}

# Stop words for keyword search
STOP_WORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been",
    "do", "does", "did", "can", "could", "will", "would", "should",
    "i", "me", "my", "we", "you", "your", "it", "its", "they",
    "this", "that", "what", "which", "how", "when", "where", "why",
    "from", "to", "in", "on", "at", "for", "of", "with", "and",
    "or", "not", "no", "if", "but", "so", "as", "by", "up",
})


# ─────────────────────────────────────────────────────────────
# Knowledge base loading (cached at module level)
# ─────────────────────────────────────────────────────────────
_knowledge_cache: Optional[list] = None


def load_knowledge_base() -> list:
    """Load the banking knowledge base from JSON file (cached)."""
    global _knowledge_cache
    if _knowledge_cache is not None:
        return _knowledge_cache
    try:
        if KNOWLEDGE_FILE.exists():
            with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                _knowledge_cache = json.load(f)
                logger.info("Loaded knowledge base: %d entries", len(_knowledge_cache))
                return _knowledge_cache
    except Exception as e:
        logger.error("Could not load knowledge base: %s", e)
    _knowledge_cache = []
    return _knowledge_cache


def keyword_search(query: str, top_k: int = 3) -> list:
    """
    Search the knowledge base using keyword matching.
    Works without any ML models or API keys.
    Returns list of matching entries sorted by relevance score.
    """
    knowledge = load_knowledge_base()
    if not knowledge:
        return []

    query_lower = query.lower().strip()
    query_words = set(re.findall(r'\w+', query_lower)) - STOP_WORDS

    scored_results = []
    for entry in knowledge:
        score = 0
        entry_text = f"{entry['question']} {entry['answer']} {entry['category']}".lower()
        entry_words = set(re.findall(r'\w+', entry_text))

        # Word overlap scoring
        meaningful_common = query_words & entry_words - STOP_WORDS
        score += len(meaningful_common) * 3

        # Question/category match boost
        for word in query_words:
            if word in entry['question'].lower():
                score += 2
            if word in entry['category'].lower():
                score += 1

        if score > 0:
            scored_results.append((score, entry))

    scored_results.sort(key=lambda x: x[0], reverse=True)
    return [entry for _, entry in scored_results[:top_k]]


# ─────────────────────────────────────────────────────────────
# Google Gemini Integration
# ─────────────────────────────────────────────────────────────
_gemini_model = None
_gemini_init_attempted = False


def _init_gemini():
    """Initialize Google Gemini model (lazy, one-time)."""
    global _gemini_model, _gemini_init_attempted
    if _gemini_init_attempted:
        return _gemini_model
    _gemini_init_attempted = True

    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key or api_key == "your_google_api_key_here":
        logger.info("No Google API key found — using keyword search fallback")
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        _gemini_model = genai.GenerativeModel("gemini-2.0-flash")
        logger.info("Google Gemini initialized successfully")
        return _gemini_model
    except ImportError:
        logger.warning("google-generativeai not installed — using keyword search")
        return None
    except Exception as e:
        logger.error("Gemini init failed: %s", e)
        return None


def query_gemini(question: str, context: str, language: str = "English") -> Optional[str]:
    """Query Google Gemini with context from knowledge base."""
    model = _init_gemini()
    if model is None:
        return None

    lang_instruction = LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["English"])

    prompt = f"""You are a helpful ATM banking assistant. Answer the user's question based on the provided context.
Be concise (2-3 sentences), accurate, and helpful. If relevant information is in the context, use it.
If the question is not related to banking/ATM services, politely redirect.

{lang_instruction}

Context:
{context}

User Question: {question}

Helpful Answer:"""

    try:
        response = model.generate_content(prompt)
        answer = response.text.strip()
        if answer:
            logger.info("Gemini response generated for: %s", question[:50])
            return answer
    except Exception as e:
        logger.warning("Gemini query failed: %s", e)

    return None


def query_rag(question: str, language: str = "English") -> str:
    """
    Query the RAG pipeline with a user question.
    Falls back gracefully: Gemini + context → Keyword search → Static fallback.
    """
    # Step 1: Get relevant context via keyword search
    results = keyword_search(question)

    # Step 2: Try Gemini with context
    if results:
        context = "\n\n".join(
            f"Q: {r['question']}\nA: {r['answer']}" for r in results[:3]
        )
        gemini_answer = query_gemini(question, context, language)
        if gemini_answer:
            return gemini_answer

        # Fallback: return best keyword match
        return results[0]["answer"]

    # Step 3: Try Gemini without context (general banking question)
    gemini_answer = query_gemini(question, "No specific context available.", language)
    if gemini_answer:
        return gemini_answer

    # Step 4: Static fallback
    return _fallback_response(question, language)


def _fallback_response(question: str, language: str) -> str:
    """Provide a basic fallback response when all search methods fail."""
    fallback = {
        "English": "I can help you with ATM services like cash withdrawal, balance inquiry, and mini statements. You can also ask me about ATM withdrawal limits, charges, card issues, and banking rules. How can I assist you?",
        "Hindi": "मैं आपकी ATM सेवाओं जैसे नकद निकासी, शेष राशि जांच, और मिनी स्टेटमेंट में मदद कर सकता हूँ। आप ATM निकासी सीमा, शुल्क, कार्ड समस्याओं और बैंकिंग नियमों के बारे में भी पूछ सकते हैं।",
        "Gujarati": "હું તમને ATM સેવાઓ જેમ કે રોકડ ઉપાડ, બેલેન્સ તપાસ અને મિની સ્ટેટમેન્ટમાં મદદ કરી શકું છું. તમે ATM ઉપાડ મર્યાદા, ચાર્જ, કાર્ડ સમસ્યાઓ અને બેંકિંગ નિયમો વિશે પણ પૂછી શકો છો.",
        "Marathi": "मी तुम्हाला ATM सेवा जसे रोख रक्कम काढणे, शिल्लक तपासणे आणि मिनी स्टेटमेंट मध्ये मदत करू शकतो. तुम्ही ATM काढण्याची मर्यादा, शुल्क, कार्ड समस्या आणि बँकिंग नियमांबद्दल देखील विचारू शकता.",
        "Tamil": "பணம் எடுப்பது, இருப்பு சோதிப்பது, மினி அறிக்கை போன்ற ATM சேவைகளில் நான் உங்களுக்கு உதவ முடியும். ATM எடுப்பு வரம்பு, கட்டணங்கள், அட்டை சிக்கல்கள் மற்றும் வங்கி விதிகள் பற்றியும் கேட்கலாம்.",
        "Telugu": "నగదు విత్‌డ్రా, బ్యాలెన్స్ చెక్, మినీ స్టేట్‌మెంట్ వంటి ATM సేవల్లో నేను మీకు సహాయం చేయగలను. ATM విత్‌డ్రా పరిమితి, ఛార్జీలు, కార్డ్ సమస్యలు మరియు బ్యాంకింగ్ నియమాల గురించి కూడా అడగవచ్చు.",
        "Bengali": "আমি আপনাকে টাকা তোলা, ব্যালেন্স চেক, মিনি স্টেটমেন্ট এর মতো ATM সেবায় সাহায্য করতে পারি। আপনি ATM তোলার সীমা, চার্জ, কার্ড সমস্যা এবং ব্যাংকিং নিয়ম সম্পর্কেও জিজ্ঞাসা করতে পারেন।",
    }
    return fallback.get(language, fallback["English"])
