"""
RAG Engine — Retrieval-Augmented Generation pipeline.
Uses LangChain + FAISS + HuggingFace Embeddings + Groq LLaMA 3.3.
Provides intelligent banking assistance and FAQ answers.
Falls back to keyword-based search when RAG components are unavailable.
"""

import json
import os
import re
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────
# Data paths
# ─────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_FILE = DATA_DIR / "banking_knowledge.json"
FAISS_INDEX_DIR = DATA_DIR / "faiss_index"

# ─────────────────────────────────────────────────────────────
# Language prompts for RAG responses
# ─────────────────────────────────────────────────────────────
LANGUAGE_INSTRUCTIONS = {
    "English": "Respond in English.",
    "Hindi": "कृपया हिंदी में उत्तर दें। Respond in Hindi language.",
    "Gujarati": "કૃપા કરીને ગુજરાતીમાં જવાબ આપો. Respond in Gujarati language.",
    "Marathi": "कृपया मराठीत उत्तर द्या. Respond in Marathi language.",
    "Tamil": "தமிழில் பதிலளிக்கவும். Respond in Tamil language.",
    "Telugu": "దయచేసి తెలుగులో సమాధానం ఇవ్వండి. Respond in Telugu language.",
    "Bengali": "অনুগ্রহ করে বাংলায় উত্তর দিন. Respond in Bengali language.",
}


# ─────────────────────────────────────────────────────────────
# Knowledge base loading (always available, no dependencies)
# ─────────────────────────────────────────────────────────────
@st.cache_data
def load_knowledge_base() -> list:
    """Load the banking knowledge base from JSON file."""
    try:
        if KNOWLEDGE_FILE.exists():
            with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        st.warning(f"Could not load knowledge base: {e}")
    return []


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
    query_words = set(re.findall(r'\w+', query_lower))

    scored_results = []
    for entry in knowledge:
        score = 0
        entry_text = f"{entry['question']} {entry['answer']} {entry['category']}".lower()
        entry_words = set(re.findall(r'\w+', entry_text))

        # Word overlap scoring
        common_words = query_words & entry_words
        # Filter out very common words
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                      "do", "does", "did", "can", "could", "will", "would", "should",
                      "i", "me", "my", "we", "you", "your", "it", "its", "they",
                      "this", "that", "what", "which", "how", "when", "where", "why",
                      "from", "to", "in", "on", "at", "for", "of", "with", "and",
                      "or", "not", "no", "if", "but", "so", "as", "by", "up"}
        meaningful_common = common_words - stop_words

        score += len(meaningful_common) * 3

        # Exact phrase matching (higher weight)
        if len(query_lower) > 3:
            # Check if key query phrases appear in the entry
            for phrase_len in range(min(5, len(query_words)), 1, -1):
                words_list = list(query_words - stop_words)
                for word in words_list:
                    if word in entry['question'].lower():
                        score += 2
                    if word in entry['category'].lower():
                        score += 1

        # Category-specific boosting
        category_keywords = {
            "withdrawal_limits": ["withdraw", "limit", "maximum", "daily", "how much", "amount"],
            "balance_inquiry": ["balance", "check", "enquiry", "inquiry", "how much"],
            "mini_statement": ["statement", "mini", "transaction", "history", "recent"],
            "pin_security": ["pin", "forgot", "change", "wrong", "block", "secure"],
            "card_issues": ["card", "lost", "stolen", "stuck", "expired", "block"],
            "charges_fees": ["charge", "fee", "cost", "free", "pay"],
            "failed_transaction": ["failed", "not received", "debited", "refund", "reverse"],
            "rbi_regulations": ["rbi", "rule", "regulation", "guideline", "policy"],
            "safety_tips": ["safe", "safety", "secure", "fraud", "scam", "skimming"],
            "general_help": ["service", "available", "what can", "options", "help"],
        }
        for cat, cat_kws in category_keywords.items():
            if entry["category"] == cat:
                for kw in cat_kws:
                    if kw in query_lower:
                        score += 2

        if score > 0:
            scored_results.append((score, entry))

    # Sort by score descending
    scored_results.sort(key=lambda x: x[0], reverse=True)
    return [entry for _, entry in scored_results[:top_k]]


# ─────────────────────────────────────────────────────────────
# Full RAG pipeline (optional, requires dependencies)
# ─────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading AI models... This may take a minute on first run.")
def init_rag_pipeline():
    """
    Initialize the RAG pipeline components.
    Returns the retrieval chain or None if setup fails.
    """
    try:
        from langchain_community.vectorstores import FAISS
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain.schema import Document

        # 1. Load knowledge base
        knowledge_data = load_knowledge_base()
        if not knowledge_data:
            return None

        # 2. Create documents
        documents = []
        for item in knowledge_data:
            content = f"Category: {item['category']}\nQuestion: {item['question']}\nAnswer: {item['answer']}"
            documents.append(Document(
                page_content=content,
                metadata={"category": item["category"], "question": item["question"]}
            ))

        # 3. Initialize embeddings (runs locally, no API key needed)
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

        # 4. Create or load FAISS index
        if FAISS_INDEX_DIR.exists():
            try:
                vector_store = FAISS.load_local(
                    str(FAISS_INDEX_DIR),
                    embeddings,
                    allow_dangerous_deserialization=True,
                )
            except Exception:
                vector_store = FAISS.from_documents(documents, embeddings)
                vector_store.save_local(str(FAISS_INDEX_DIR))
        else:
            vector_store = FAISS.from_documents(documents, embeddings)
            FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)
            vector_store.save_local(str(FAISS_INDEX_DIR))

        # 5. Set up Groq LLM
        groq_api_key = os.getenv("GROQ_API_KEY", "")
        if not groq_api_key or groq_api_key == "your_groq_api_key_here":
            return {"vector_store": vector_store, "chain": None, "mode": "retrieval_only"}

        from langchain_groq import ChatGroq
        from langchain.chains import create_retrieval_chain
        from langchain.chains.combine_documents import create_stuff_documents_chain
        from langchain_core.prompts import ChatPromptTemplate

        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            api_key=groq_api_key,
        )

        # 6. Build retrieval chain
        prompt = ChatPromptTemplate.from_template("""
You are a helpful ATM banking assistant. Answer the user's question based on the provided context.
Be concise, accurate, and helpful. If relevant information is in the context, use it.
If the question is not related to banking/ATM services, politely redirect.

{language_instruction}

Context:
{context}

User Question: {input}

Helpful Answer:""")

        retriever = vector_store.as_retriever(search_kwargs={"k": 3})
        document_chain = create_stuff_documents_chain(llm, prompt)
        retrieval_chain = create_retrieval_chain(retriever, document_chain)

        return {"vector_store": vector_store, "chain": retrieval_chain, "mode": "full_rag"}

    except ImportError as e:
        # Missing dependencies — fall back to keyword search
        return None
    except Exception as e:
        # Any other error — fall back to keyword search
        return None


def query_rag(question: str, language: str = "English") -> str:
    """
    Query the RAG pipeline with a user question.
    Falls back gracefully: Full RAG → FAISS retrieval → Keyword search → Static response.
    """
    language_instruction = LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["English"])

    # ── Attempt 1: Full RAG pipeline ──
    rag = init_rag_pipeline()

    if rag is not None:
        try:
            if rag["mode"] == "full_rag" and rag["chain"] is not None:
                response = rag["chain"].invoke({
                    "input": question,
                    "language_instruction": language_instruction,
                })
                answer = response.get("answer", "")
                if answer:
                    return answer

            # Retrieval-only mode (FAISS without LLM)
            if rag.get("vector_store"):
                docs = rag["vector_store"].similarity_search(question, k=3)
                if docs:
                    best_doc = docs[0].page_content
                    if "Answer:" in best_doc:
                        return best_doc.split("Answer:")[-1].strip()
                    return best_doc

        except Exception:
            pass  # Fall through to keyword search

    # ── Attempt 2: Keyword-based search (no ML needed) ──
    results = keyword_search(question)
    if results:
        # Return the best matching answer
        best = results[0]
        answer = best["answer"]

        # If multiple good matches, combine top 2
        if len(results) >= 2:
            answer = f"{best['answer']}"

        return answer

    # ── Attempt 3: Static fallback ──
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
