# 🏧 Smart ATM — RAG-Based Multilingual Voice Chatbot

A **voice-enabled multilingual ATM chatbot** built with Streamlit, powered by **RAG (Retrieval-Augmented Generation)** for intelligent banking assistance. Supports **7 Indian languages** with speech-to-text and text-to-speech capabilities.

---

## ✨ Features

- 🎤 **Voice Interaction** — Speak commands in any supported Indian language
- 🌐 **7 Indian Languages** — English, Hindi, Gujarati, Marathi, Tamil, Telugu, Bengali
- 🧠 **RAG-Powered Responses** — Intelligent FAQ answers using LangChain + FAISS + Groq
- 🔐 **Secure PIN Entry** — PIN entered only via keypad (never voice)
- 💰 **Transaction Simulation** — Withdraw, check balance, mini-statement
- 🎨 **Premium UI** — Glassmorphism dark theme with animations

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Frontend | Streamlit |
| STT | SpeechRecognition (Google API) |
| TTS | gTTS |
| NLP | Rule-based intent classification |
| LLM | Groq (LLaMA 3.3 70B) |
| Embeddings | HuggingFace (all-MiniLM-L6-v2) |
| Vector DB | FAISS |
| RAG Framework | LangChain 0.3.x |

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- Groq API key (free at [console.groq.com](https://console.groq.com))

### 2. Install Dependencies

```bash
cd ATM
pip install -r requirements.txt
```

### 3. Configure API Key

```bash
# Create .env file
copy .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 4. Run the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## 🔑 Demo Credentials

- **PIN:** `1234`
- **Account Balance:** ₹25,000

## 📁 Project Structure

```
ATM/
├── app.py                    # Main Streamlit application
├── .streamlit/config.toml    # Theme configuration
├── src/
│   ├── nlp_engine.py         # Intent & entity extraction
│   ├── rag_engine.py         # RAG pipeline
│   ├── speech_engine.py      # STT + TTS
│   ├── transaction_engine.py # Transaction simulation
│   ├── security.py           # PIN & session management
│   └── translations.py       # Multilingual text
├── data/
│   └── banking_knowledge.json # 48-entry knowledge base
├── assets/
│   └── style.css             # Glassmorphism CSS
└── requirements.txt
```

## 🔒 Security

- PIN is **never spoken, logged, or stored in plaintext**
- bcrypt hashing for PIN verification
- 3-attempt lockout with 30-second cooldown
- Auto session timeout after 2 minutes
- Audio processed in-memory only

## 📄 License

MIT License
