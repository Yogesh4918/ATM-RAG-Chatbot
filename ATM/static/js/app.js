/**
 * Smart ATM Chatbot — Frontend JavaScript
 * Handles: Chat, Voice (Web Speech API), PIN Keypad, Transactions, TTS
 */

// ═══════════════════════════════════════════════════════════
// State
// ═══════════════════════════════════════════════════════════
let currentLang = 'English';
let isListening = false;
let recognition = null;
let pinDigits = '';
let translations = {};

// ═══════════════════════════════════════════════════════════
// Init
// ═══════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
    loadTranslations();
    checkSession();
    initSpeechRecognition();
    document.getElementById('languageSelect').addEventListener('change', changeLanguage);
});

// ═══════════════════════════════════════════════════════════
// API Helpers
// ═══════════════════════════════════════════════════════════
async function api(endpoint, data = null) {
    const opts = { headers: { 'Content-Type': 'application/json' } };
    if (data) {
        opts.method = 'POST';
        opts.body = JSON.stringify(data);
    }
    const res = await fetch(endpoint, opts);
    return res.json();
}

// ═══════════════════════════════════════════════════════════
// Session Management
// ═══════════════════════════════════════════════════════════
async function checkSession() {
    const data = await api('/api/session-status');
    currentLang = data.language;
    document.getElementById('languageSelect').value = currentLang;

    if (data.card_inserted) {
        showScreen('chatScreen');
        updateSessionUI(data);
    } else {
        showScreen('cardInsertScreen');
    }

    if (data.timed_out) {
        addBotMessage(translations.session_timeout || 'Session timed out.');
    }
}

async function insertCard() {
    const data = await api('/api/insert-card', {});
    showScreen('chatScreen');
    addBotMessage(data.message);
    speak(data.message);
    updateSessionUI({ card_inserted: true, pin_verified: false });
    document.getElementById('quickActionsSection').style.display = 'block';
    document.getElementById('endSessionBtn').style.display = 'block';

    const status = document.getElementById('cardStatus');
    status.innerHTML = '<span class="status-dot active"></span><span>Card Inserted</span>';
}

async function endSession() {
    const data = await api('/api/end-session', {});
    addBotMessage(data.message);
    speak(data.message);
    setTimeout(() => {
        clearChat();
        showScreen('cardInsertScreen');
        document.getElementById('quickActionsSection').style.display = 'none';
        document.getElementById('endSessionBtn').style.display = 'none';
        document.getElementById('accountInfo').style.display = 'none';
        document.getElementById('authStatus').style.display = 'none';
        const status = document.getElementById('cardStatus');
        status.innerHTML = '<span class="status-dot inactive"></span><span>No Card</span>';
    }, 2000);
}

function updateSessionUI(data) {
    if (data.pin_verified) {
        document.getElementById('authStatus').style.display = 'flex';
        document.getElementById('accountInfo').style.display = 'block';
        if (data.balance !== undefined) {
            document.getElementById('balDisplay').textContent = formatCurrency(data.balance);
        }
        if (data.card_number) {
            document.getElementById('cardNum').textContent = data.card_number;
        }
    }
    const status = document.getElementById('cardStatus');
    if (data.card_inserted) {
        status.innerHTML = '<span class="status-dot active"></span><span>Card Inserted</span>';
    }
}

// ═══════════════════════════════════════════════════════════
// Language
// ═══════════════════════════════════════════════════════════
async function changeLanguage() {
    currentLang = document.getElementById('languageSelect').value;
    await api('/api/set-language', { language: currentLang });
    await loadTranslations();
    updateUIText();
}

async function loadTranslations() {
    translations = await api(`/api/translations?language=${currentLang}`);
}

function updateUIText() {
    const t = translations;
    if (!t) return;
    setText('langLabel', t.select_language);
    setText('insertCardTitle', t.insert_card);
    setText('qaLabel', t.quick_actions);
    setText('qWithdraw', t.withdraw);
    setText('qBalance', t.balance);
    setText('qStatement', t.mini_statement);
    setText('qHelp', t.help_faq);
    setText('exitLabel', t.exit_session);
    setText('pinSecNote', t.pin_security_note?.replace('🔒 ', '') || 'PIN can only be entered via keypad');
    setText('voiceLabel', t.voice_input);
    setText('textLabel', t.text_input);
    setText('micLabel', t.mic_button?.replace('🎙️ ', '') || 'Press to Speak');
    setText('emptyMsg', t.ask_anything);
    setText('amountTitle', t.enter_amount);
    setText('cardNumLabel', t.card_number);
    setText('balLabel', t.available_balance);
    const input = document.getElementById('chatInput');
    if (input) input.placeholder = t.type_message || 'Type your message...';
}

function setText(id, text) {
    const el = document.getElementById(id);
    if (el && text) el.textContent = text;
}

// ═══════════════════════════════════════════════════════════
// Chat
// ═══════════════════════════════════════════════════════════
function addUserMessage(text) {
    hideEmpty();
    const container = document.getElementById('chatContainer');
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const div = document.createElement('div');
    div.className = 'chat-msg user';
    div.innerHTML = `
        <div class="msg-bubble user">
            ${escapeHtml(text)}
            <div class="msg-time">${time}</div>
        </div>
        <div class="msg-avatar user">👤</div>
    `;
    container.appendChild(div);
    scrollChat();
}

function addBotMessage(text) {
    hideEmpty();
    const container = document.getElementById('chatContainer');
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const div = document.createElement('div');
    div.className = 'chat-msg bot';
    div.innerHTML = `
        <div class="msg-avatar bot">🏧</div>
        <div class="msg-bubble bot">
            ${escapeHtml(text)}
            <div class="msg-time">${time}</div>
        </div>
    `;
    container.appendChild(div);
    scrollChat();
}

function addLoadingMessage() {
    hideEmpty();
    const container = document.getElementById('chatContainer');
    const div = document.createElement('div');
    div.className = 'chat-msg bot';
    div.id = 'loadingMsg';
    div.innerHTML = `
        <div class="msg-avatar bot">🏧</div>
        <div class="msg-bubble bot">
            <div class="loading-dots"><span></span><span></span><span></span></div>
        </div>
    `;
    container.appendChild(div);
    scrollChat();
}

function removeLoading() {
    const el = document.getElementById('loadingMsg');
    if (el) el.remove();
}

function clearChat() {
    const container = document.getElementById('chatContainer');
    container.innerHTML = `<div class="chat-empty" id="chatEmpty"><div class="empty-icon">💬</div><p id="emptyMsg">${translations.ask_anything || 'Ask me anything!'}</p></div>`;
    document.getElementById('receiptArea').innerHTML = '';
    document.getElementById('statementArea').innerHTML = '';
}

function hideEmpty() {
    const empty = document.getElementById('chatEmpty');
    if (empty) empty.style.display = 'none';
}

function scrollChat() {
    const container = document.getElementById('chatContainer');
    container.scrollTop = container.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(id).classList.add('active');
}

// ═══════════════════════════════════════════════════════════
// Text Input
// ═══════════════════════════════════════════════════════════
async function sendText(e) {
    e.preventDefault();
    const input = document.getElementById('chatInput');
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    await processInput(text);
}

async function processInput(text) {
    addUserMessage(text);
    addLoadingMessage();

    const data = await api('/api/process', { text });
    removeLoading();
    handleResponse(data);
}

function handleResponse(data) {
    if (!data) return;

    switch (data.type) {
        case 'greeting':
        case 'help':
        case 'faq':
            addBotMessage(data.message);
            speak(data.message);
            break;

        case 'goodbye':
            addBotMessage(data.message);
            speak(data.message);
            setTimeout(() => {
                clearChat();
                showScreen('cardInsertScreen');
                document.getElementById('quickActionsSection').style.display = 'none';
                document.getElementById('endSessionBtn').style.display = 'none';
                document.getElementById('accountInfo').style.display = 'none';
                document.getElementById('authStatus').style.display = 'none';
                document.getElementById('cardStatus').innerHTML = '<span class="status-dot inactive"></span><span>No Card</span>';
            }, 2500);
            break;

        case 'need_pin':
            addBotMessage('🔐 ' + data.message);
            speak(data.message);
            showPinModal();
            break;

        case 'need_amount':
            addBotMessage('💵 ' + data.message);
            document.getElementById('amountArea').style.display = 'block';
            document.getElementById('inputArea').style.display = 'none';
            break;

        case 'balance':
            addBotMessage('💰 ' + data.message);
            speak(data.message);
            updateBalance(data.balance);
            break;

        case 'mini_statement':
            addBotMessage('📋 ' + data.message);
            speak(data.message);
            renderStatement(data);
            break;

        case 'withdraw_success':
            addBotMessage('✅ ' + data.message);
            addBotMessage('📦 ' + data.collect_msg);
            speak(data.message);
            renderReceipt(data.receipt);
            updateBalance(data.receipt.available_balance);
            break;

        case 'error':
            addBotMessage('❌ ' + data.message);
            speak(data.message);
            break;

        case 'timeout':
            addBotMessage('⏰ ' + data.message);
            speak(data.message);
            setTimeout(() => location.reload(), 2000);
            break;

        default:
            if (data.message) {
                addBotMessage(data.message);
                speak(data.message);
            }
    }
}

function updateBalance(bal) {
    document.getElementById('balDisplay').textContent = formatCurrency(bal);
    document.getElementById('accountInfo').style.display = 'block';
    document.getElementById('authStatus').style.display = 'flex';
}

// ═══════════════════════════════════════════════════════════
// Quick Actions
// ═══════════════════════════════════════════════════════════
async function quickAction(action) {
    const labels = {
        withdraw: translations.withdraw || 'Withdraw',
        balance: translations.balance || 'Balance',
        mini_statement: translations.mini_statement || 'Mini Statement',
        help: translations.help_faq || 'Help',
    };

    addUserMessage('⚡ ' + labels[action]);

    if (action === 'help') {
        addLoadingMessage();
        const data = await api('/api/process', { text: 'What services are available at ATM?' });
        removeLoading();
        if (data.message) {
            addBotMessage('🧠 ' + data.message);
            speak(data.message);
        }
        return;
    }

    addLoadingMessage();
    const data = await api('/api/process', { text: action === 'withdraw' ? 'withdraw money' : action === 'balance' ? 'check balance' : 'mini statement' });
    removeLoading();
    handleResponse(data);
}

// ═══════════════════════════════════════════════════════════
// Amount Input
// ═══════════════════════════════════════════════════════════
function setAmount(val) {
    document.getElementById('amountInput').value = val;
}

async function confirmWithdraw() {
    const amount = parseInt(document.getElementById('amountInput').value);
    if (!amount || amount < 100) return;
    document.getElementById('amountArea').style.display = 'none';
    document.getElementById('inputArea').style.display = 'block';

    addUserMessage(`💵 ${formatCurrency(amount)}`);
    addLoadingMessage();
    const data = await api('/api/withdraw', { amount });
    removeLoading();
    handleResponse(data);
}

function cancelAmount() {
    document.getElementById('amountArea').style.display = 'none';
    document.getElementById('inputArea').style.display = 'block';
}

// ═══════════════════════════════════════════════════════════
// PIN Keypad
// ═══════════════════════════════════════════════════════════
function showPinModal() {
    pinDigits = '';
    updatePinDisplay();
    document.getElementById('pinError').textContent = '';
    document.getElementById('pinModal').style.display = 'flex';
}

function hidePinModal() {
    document.getElementById('pinModal').style.display = 'none';
    pinDigits = '';
}

function pinKey(digit) {
    if (pinDigits.length < 4) {
        pinDigits += digit;
        updatePinDisplay();
        // Auto-submit on 4 digits
        if (pinDigits.length === 4) {
            setTimeout(pinSubmit, 300);
        }
    }
}

function pinClear() {
    pinDigits = pinDigits.slice(0, -1);
    updatePinDisplay();
}

function updatePinDisplay() {
    const filled = pinDigits.length;
    let display = '';
    for (let i = 0; i < 4; i++) {
        display += i < filled ? '● ' : '○ ';
    }
    document.getElementById('pinDisplay').textContent = display.trim();
}

async function pinSubmit() {
    if (pinDigits.length !== 4) return;

    const data = await api('/api/validate-pin', { pin: pinDigits });
    pinDigits = '';
    updatePinDisplay();

    if (data.success) {
        hidePinModal();
        addBotMessage('✅ ' + data.message);
        speak(data.message);
        updateSessionUI({ pin_verified: true, card_inserted: true });

        // Handle action result from pending action
        if (data.action_result) {
            handleResponse(data.action_result);
        }

        // Refresh session info
        const status = await api('/api/session-status');
        updateSessionUI(status);
    } else {
        document.getElementById('pinError').textContent = data.message;
        if (data.locked) {
            setTimeout(hidePinModal, 2000);
            addBotMessage('🔒 ' + data.message);
            speak(data.message);
        }
    }
}

// ═══════════════════════════════════════════════════════════
// Receipt & Statement Rendering
// ═══════════════════════════════════════════════════════════
function renderReceipt(receipt) {
    const area = document.getElementById('receiptArea');
    area.innerHTML = `
    <div class="receipt-card">
        <h3>🧾 ${translations.transaction_receipt || 'Transaction Receipt'}</h3>
        <div class="receipt-row"><span class="label">${translations.card_number || 'Card'}</span><span class="value">${receipt.card_number}</span></div>
        <div class="receipt-row"><span class="label">${translations.date_time || 'Date'}</span><span class="value">${receipt.date_time}</span></div>
        <div class="receipt-row"><span class="label">${translations.transaction_type || 'Type'}</span><span class="value">${receipt.transaction_type}</span></div>
        <div class="receipt-row"><span class="label">${translations.amount || 'Amount'}</span><span class="value" style="color:var(--accent-green)">${receipt.formatted_amount}</span></div>
        <div class="receipt-row"><span class="label">${translations.available_balance || 'Balance'}</span><span class="value">${receipt.formatted_balance}</span></div>
        <div class="receipt-row"><span class="label">Ref No.</span><span class="value">${receipt.reference_no}</span></div>
    </div>`;
    scrollChat();
}

function renderStatement(data) {
    let rows = '';
    (data.transactions || []).forEach(tx => {
        const cls = tx.type === 'Credit' ? 'tx-credit' : 'tx-debit';
        const sign = tx.type === 'Credit' ? '+' : '-';
        rows += `<tr><td>${tx.date}</td><td>${tx.description}</td><td class="${cls}">${sign}${formatCurrency(tx.amount)}</td><td>${formatCurrency(tx.balance)}</td></tr>`;
    });

    const area = document.getElementById('statementArea');
    area.innerHTML = `
    <div class="statement-card">
        <h3>📋 ${translations.mini_statement || 'Mini Statement'}</h3>
        <table class="stmt-table">
            <thead><tr><th>${translations.date_time || 'Date'}</th><th>${translations.transaction_type || 'Type'}</th><th>${translations.amount || 'Amount'}</th><th>${translations.available_balance || 'Balance'}</th></tr></thead>
            <tbody>${rows}</tbody>
        </table>
        <div class="stmt-balance">${translations.available_balance || 'Balance'}: ${data.formatted_balance}</div>
    </div>`;
    scrollChat();
}

// ═══════════════════════════════════════════════════════════
// Voice (Web Speech API)
// ═══════════════════════════════════════════════════════════
const STT_LOCALES = {
    English: 'en-IN', Hindi: 'hi-IN', Gujarati: 'gu-IN',
    Marathi: 'mr-IN', Tamil: 'ta-IN', Telugu: 'te-IN', Bengali: 'bn-IN'
};

function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        console.warn('Speech Recognition not supported');
        return;
    }
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = (event) => {
        const text = event.results[0][0].transcript;
        stopListening();
        processInput(text);
    };

    recognition.onerror = (event) => {
        console.error('STT error:', event.error);
        stopListening();
        if (event.error !== 'aborted') {
            addBotMessage('⚠️ Could not understand audio. Please try again.');
        }
    };

    recognition.onend = () => stopListening();
}

function toggleVoice() {
    if (isListening) {
        recognition?.abort();
        stopListening();
    } else {
        startListening();
    }
}

function startListening() {
    if (!recognition) {
        addBotMessage('⚠️ Voice input is not supported in this browser. Please use Chrome.');
        return;
    }
    isListening = true;
    recognition.lang = STT_LOCALES[currentLang] || 'en-IN';
    const btn = document.getElementById('micBtn');
    btn.classList.add('listening');
    document.getElementById('micLabel').textContent = translations.listening || 'Listening...';
    try { recognition.start(); } catch (e) { stopListening(); }
}

function stopListening() {
    isListening = false;
    const btn = document.getElementById('micBtn');
    btn.classList.remove('listening');
    document.getElementById('micLabel').textContent =
        (translations.mic_button || '🎙️ Press to Speak').replace('🎙️ ', '');
}

// ═══════════════════════════════════════════════════════════
// TTS (via backend gTTS)
// ═══════════════════════════════════════════════════════════
async function speak(text) {
    if (!text) return;
    // Clean text of emojis for TTS
    const cleanText = text.replace(/[\u{1F000}-\u{1FFFF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[✅❌🔐💰📋📦⚡🧠⏰🔒💵]/gu, '').trim();
    if (!cleanText) return;

    try {
        const res = await fetch('/api/tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: cleanText, language: currentLang })
        });
        if (res.ok) {
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const audio = document.getElementById('ttsAudio');
            audio.src = url;
            audio.play().catch(() => {});
        }
    } catch (e) {
        console.warn('TTS error:', e);
    }
}

// ═══════════════════════════════════════════════════════════
// UI Tabs & Sidebar
// ═══════════════════════════════════════════════════════════
function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    if (tab === 'voice') {
        document.getElementById('voiceTab').classList.add('active');
        document.getElementById('voiceContent').classList.add('active');
    } else {
        document.getElementById('textTab').classList.add('active');
        document.getElementById('textContent').classList.add('active');
        setTimeout(() => document.getElementById('chatInput')?.focus(), 100);
    }
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
}

// Close sidebar on overlay click (mobile)
document.addEventListener('click', (e) => {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('sidebarToggle');
    if (sidebar.classList.contains('open') && !sidebar.contains(e.target) && !toggle.contains(e.target)) {
        sidebar.classList.remove('open');
    }
});

// ═══════════════════════════════════════════════════════════
// Utility
// ═══════════════════════════════════════════════════════════
function formatCurrency(amount) {
    const s = String(Math.abs(parseInt(amount)));
    if (s.length <= 3) return '₹' + s;
    const last3 = s.slice(-3);
    let rest = s.slice(0, -3);
    const groups = [];
    while (rest.length > 2) { groups.unshift(rest.slice(-2)); rest = rest.slice(0, -2); }
    if (rest) groups.unshift(rest);
    return '₹' + groups.join(',') + ',' + last3;
}
