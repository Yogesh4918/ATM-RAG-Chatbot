# 🏧 Smart ATM — RAG-Based Multilingual Voice Chatbot

A **voice-enabled multilingual ATM chatbot** with a premium glassmorphism dark UI, powered by **Flask + HTML/CSS/JS**. Supports **7 Indian languages** with browser-native speech recognition and text-to-speech.

---

## ✨ Features

- 🎤 **Voice Interaction** — Browser-native Web Speech API for instant voice commands
- 🌐 **7 Indian Languages** — English, Hindi, Gujarati, Marathi, Tamil, Telugu, Bengali
- 🧠 **AI-Powered Responses** — Keyword-based knowledge search over 48+ banking FAQs
- 🔐 **Secure PIN Entry** — PIN entered only via on-screen keypad (never voice)
- 💰 **Transaction Simulation** — Withdraw, check balance, mini-statement
- 🎨 **Premium UI** — Glassmorphism dark theme with animations & micro-interactions
- 📱 **Fully Responsive** — Works on mobile, tablet, and desktop
- ⚡ **Real-Time** — Single-page app with no page reloads

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Backend | Flask (Python) |
| Frontend | HTML5 + CSS3 + Vanilla JavaScript |
| Voice Input (STT) | Web Speech API (browser-native) |
| Voice Output (TTS) | gTTS (Google Text-to-Speech) |
| NLP | Keyword-based multilingual intent classification |
| Knowledge Base | JSON (48 banking FAQ entries) |
| Design | Glassmorphism, CSS animations, responsive grid |

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- Chrome or Edge browser (for voice input)

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install directly:

```bash
pip install flask python-dotenv gTTS bcrypt
```

### 3. Run the App

```bash
python d:\ATM\app.py
```

The app will open at **http://localhost:5000**

## 🔑 Demo Credentials

- **PIN:** `1234`
- **Account Balance:** ₹25,000

## 📁 Project Structure

```
ATM/
├── app.py                       # Flask backend + REST API
├── templates/
│   └── index.html               # Main HTML page
├── static/
│   ├── css/style.css            # Glassmorphism responsive CSS
│   └── js/app.js                # Frontend SPA logic
├── src/
│   ├── translations.py          # 7-language UI translations
│   ├── security.py              # PIN hashing & session mgmt
│   ├── nlp_engine.py            # Multilingual intent classifier
│   ├── transaction_engine.py    # Banking simulation
│   ├── speech_engine.py         # STT + TTS helpers
│   └── rag_engine.py            # Knowledge search engine
├── data/
│   └── banking_knowledge.json   # 48-entry banking FAQ
├── requirements.txt
└── README.md
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Serve frontend |
| GET | `/api/session-status` | Get current session state |
| POST | `/api/insert-card` | Start ATM session |
| POST | `/api/set-language` | Change UI language |
| POST | `/api/process` | Process text input (NLP) |
| POST | `/api/validate-pin` | Validate PIN entry |
| POST | `/api/withdraw` | Execute cash withdrawal |
| POST | `/api/tts` | Generate speech audio |
| POST | `/api/end-session` | End ATM session |
| GET | `/api/translations` | Get UI text for language |

## 🎨 UI Highlights

- **Glassmorphism** — Frosted glass cards with backdrop blur
- **Neon Accents** — Cyan (#00f2ff) and purple (#7b2ff7) gradients
- **Animated Background** — Rotating conic gradient mesh
- **Micro-Animations** — Floating card, pulsing mic, sliding messages
- **Custom PIN Keypad** — Modal with circular buttons and auto-submit
- **Transaction Receipts** — Styled receipt cards with animated shine

## 🔒 Security

- PIN is **never spoken, logged, or stored in plaintext**
- SHA-256 hashing for PIN verification
- 3-attempt lockout with 30-second cooldown
- Auto session timeout after 2 minutes
- PIN accepted **only via on-screen keypad**

## 📱 Responsive Breakpoints

| Device | Width | Adjustments |
|---|---|---|
| Desktop | > 768px | Full sidebar + chat layout |
| Tablet | 481–768px | Collapsible sidebar, adjusted spacing |
| Mobile | ≤ 480px | Hamburger menu, compact keypad |

## 📄 License

MIT License
