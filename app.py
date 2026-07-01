"""
app.py
------
MediBot — a focused, polished Streamlit chatbot that helps hospital patients & visitors.

Run locally:
    streamlit run app.py

Features a custom chat UI (styled bubbles, hospital header, quick-question chips),
strict medical-safety behaviour, reliable fallback for out-of-scope questions, and
graceful handling of empty input and API errors. Works with no API key (offline demo
mode) and upgrades to the Google Gemini API automatically when a key is present.
"""

import html

import streamlit as st
from dotenv import load_dotenv

try:
    import markdown as _md

    def md_to_html(text: str) -> str:
        return _md.markdown(text, extensions=["extra", "sane_lists", "nl2br"])
except Exception:  # markdown not installed -> safe minimal fallback
    def md_to_html(text: str) -> str:
        return "<p>" + html.escape(text).replace("\n", "<br>") + "</p>"

from knowledge import (
    BOT_NAME,
    HOSPITAL_NAME,
    HELPLINE,
    EMERGENCY_NUMBER,
    ADDRESS,
    WEBSITE,
    SUGGESTED_QUESTIONS,
)
from llm import generate_reply, provider_label, active_provider, LLMError

load_dotenv()

st.set_page_config(
    page_title=f"{BOT_NAME} · {HOSPITAL_NAME}",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="expanded",
)

WELCOME_MESSAGE = (
    f"👋 Hello! I'm **{BOT_NAME}**, your assistant at **{HOSPITAL_NAME}**.\n\n"
    "I can help you with **appointments**, **OPD & visiting timings**, **departments**, "
    "**services**, and **emergency info**.\n\n"
    "_Note: I can't give medical advice or diagnoses — for that, I'll help you book with a doctor._"
)

# ---------------------------------------------------------------------------
# THEME  (custom CSS)
# ---------------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

:root {
  --bg-dark: #070b13;
  --brand-1: #0ea5e9; /* Cyan 500 */
  --brand-2: #2dd4bf; /* Teal 400 */
  --brand-3: #6366f1; /* Indigo 500 */
  --ink: #f8fafc;
  --muted: #94a3b8;
  --line: rgba(255, 255, 255, 0.08);
  --bot-bg: rgba(30, 41, 59, 0.45);
  --danger: #f43f5e;
  --ok: #10b981;
  --card-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
  --hero-shadow: 0 20px 40px -15px rgba(14, 165, 233, 0.25);
}

/* App background + typography */
.stApp {
  background:
    radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.15) 0px, transparent 50%),
    radial-gradient(at 100% 0%, rgba(45, 212, 191, 0.15) 0px, transparent 50%),
    radial-gradient(at 50% 100%, rgba(14, 165, 233, 0.12) 0px, transparent 50%),
    var(--bg-dark);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  -webkit-font-smoothing: antialiased;
  color: var(--ink);
}

/* Make sure text elements in Streamlit render cleanly in dark mode */
.stApp p, .stApp span, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
  color: var(--ink) !important;
}

header[data-testid="stHeader"] {
  background: transparent !important;
}

footer {
  visibility: hidden;
}

#MainMenu {
  visibility: hidden;
}

.block-container {
  padding-top: 2rem;
  padding-bottom: 7rem;
  max-width: 800px;
}

/* ---- Hospital header card (Hero) ---- */
.hero {
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.7) 0%, rgba(30, 41, 59, 0.7) 100%);
  border-radius: 24px;
  padding: 24px 28px;
  color: #fff;
  box-shadow: var(--hero-shadow);
  display: flex;
  align-items: center;
  gap: 20px;
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  margin-bottom: 1.5rem;
}

/* Animated background glow circles */
.hero::before {
  content: "";
  position: absolute;
  right: -30px;
  top: -30px;
  width: 150px;
  height: 150px;
  background: radial-gradient(circle, rgba(45, 212, 191, 0.15) 0%, rgba(255,255,255,0) 70%);
  border-radius: 50%;
}

.hero::after {
  content: "";
  position: absolute;
  left: 20%;
  bottom: -50px;
  width: 120px;
  height: 120px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.1) 0%, rgba(255,255,255,0) 70%);
  border-radius: 50%;
}

.hero-logo {
  width: 64px;
  height: 64px;
  min-width: 64px;
  border-radius: 20px;
  background: rgba(14, 165, 233, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(14, 165, 233, 0.35);
  box-shadow: 0 0 20px rgba(14, 165, 233, 0.25);
  animation: float 4s ease-in-out infinite;
}

@keyframes float {
  0% { transform: translateY(0px); }
  50% { transform: translateY(-6px); }
  100% { transform: translateY(0px); }
}

.hero-txt h1 {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 1.85rem;
  font-weight: 800;
  margin: 0;
  line-height: 1.2;
  letter-spacing: -0.02em;
  background: linear-gradient(135deg, #ffffff 30%, #38bdf8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.hero-txt p {
  margin: 4px 0 0;
  opacity: 0.85;
  font-size: 0.95rem;
  font-weight: 500;
  color: #94a3b8 !important;
}

.hero-badges {
  display: flex;
  gap: 10px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8rem;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 6px 14px;
  border-radius: 999px;
  backdrop-filter: blur(4px);
  transition: all 0.3s ease;
  color: #f1f5f9 !important;
}

.badge:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--ok);
  box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
  }
  70% {
    box-shadow: 0 0 0 8px rgba(16, 185, 129, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
  }
}

.badge.emg {
  background: rgba(244, 63, 94, 0.15);
  border-color: rgba(244, 63, 94, 0.3);
  font-weight: 700;
}

/* ---- Chat bubbles ---- */
.msg-row {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  margin: 20px 0;
  animation: slideUp 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.msg-row.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 40px;
  height: 40px;
  min-width: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
}

.bot-avatar {
  background: linear-gradient(135deg, var(--brand-1), var(--brand-3));
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.user-avatar {
  background: rgba(255, 255, 255, 0.08);
  color: #cbd5e1;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.bubble {
  max-width: 78%;
  padding: 16px 20px;
  border-radius: 20px;
  font-size: 0.98rem;
  line-height: 1.6;
  box-shadow: var(--card-shadow);
  transition: transform 0.2s ease;
}

.bot-bubble {
  background: var(--bot-bg);
  color: #cbd5e1;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-bottom-left-radius: 4px;
}

.bot-bubble p, .bot-bubble span, .bot-bubble li {
  color: #cbd5e1 !important;
}

.user-bubble {
  background: linear-gradient(135deg, #0d9488 0%, #1e1b4b 100%);
  color: #fff;
  border: 1px solid rgba(45, 212, 191, 0.25);
  border-bottom-right-radius: 4px;
}

.user-bubble p, .user-bubble span {
  color: #ffffff !important;
}

.bubble p {
  margin: 0 0 0.75rem;
}

.bubble p:last-child {
  margin-bottom: 0;
}

.bubble ul, .bubble ol {
  margin: 0.5rem 0 0.5rem 1.25rem;
  padding: 0;
}

.bubble li {
  margin: 0.25rem 0;
}

.bubble a {
  color: #38bdf8;
  text-decoration: underline;
  font-weight: 500;
}

.user-bubble strong {
  color: #fff;
}

/* Typing dots */
.typing {
  display: flex;
  gap: 6px;
  padding: 8px 10px;
  align-items: center;
}

.typing span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #38bdf8;
  animation: bounce 1.4s infinite ease-in-out both;
}

.typing span:nth-child(1) { animation-delay: -0.32s; }
.typing span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* ---- Quick-question chips (Streamlit buttons) ---- */
.chips-label {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--muted);
  margin: 16px 4px 8px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

/* ---- Chat input ---- */
/* Make the entire bottom container and all its inner wrapper divs transparent */
div[data-testid="stBottom"],
div[data-testid="stBottomBlockContainer"],
footer + div,
div[data-testid="stBottom"] > div,
div[data-testid="stBottomBlockContainer"] > div,
footer + div > div {
  background: transparent !important;
  background-color: transparent !important;
  box-shadow: none !important;
  border: none !important;
}

/* Restore and style the background and border on the chat input container specifically */
[data-testid="stChatInput"] {
  border-radius: 20px !important;
  border: 1.5px solid rgba(255, 255, 255, 0.22) !important; /* Premium visible border */
  box-shadow: 0 15px 45px -10px rgba(0, 0, 0, 0.5) !important;
  background: rgba(15, 23, 42, 0.85) !important;
  background-color: rgba(15, 23, 42, 0.85) !important;
  padding: 6px !important;
  backdrop-filter: blur(16px);
  transition: border-color 0.25s ease, box-shadow 0.25s ease !important;
}

/* Add a beautiful cyan glow on focus-within */
[data-testid="stChatInput"]:focus-within {
  border-color: rgba(45, 212, 191, 0.5) !important;
  box-shadow: 0 0 15px rgba(45, 212, 191, 0.25), 0 15px 45px -10px rgba(0, 0, 0, 0.5) !important;
}

[data-testid="stChatInput"] textarea {
  font-size: 0.98rem !important;
  line-height: 1.5 !important;
  color: #ffffff !important;
}

/* Sidebar action button custom styling */
section[data-testid="stSidebar"] button {
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  color: #cbd5e1 !important;
  border-radius: 12px !important;
  font-weight: 600 !important;
  transition: all 0.2s ease !important;
}

section[data-testid="stSidebar"] button:hover {
  background: rgba(244, 63, 94, 0.15) !important;
  border-color: rgba(244, 63, 94, 0.3) !important;
  color: #f43f5e !important;
  transform: translateY(-1px);
}


/* ---- Sidebar ---- */
section[data-testid="stSidebar"] {
  background-color: #05080f !important;
  background-image: radial-gradient(circle at 0% 0%, #0d1527 0%, #05080f 100%) !important;
  border-right: 1px solid rgba(255,255,255,0.04);
}

section[data-testid="stSidebar"] * {
  color: #cbd5e1 !important;
}

.sb-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 20px;
  padding: 18px 20px;
  margin-bottom: 16px;
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(10px);
}

.sb-card h3 {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 1.15rem;
  font-weight: 700;
  margin: 0 0 4px;
  color: #ffffff !important;
}

.sb-card .sub {
  font-size: 0.82rem;
  color: #64748b !important;
  margin-bottom: 14px;
}

.sb-row {
  display: flex;
  gap: 12px;
  font-size: 0.88rem;
  margin: 10px 0;
  align-items: flex-start;
  line-height: 1.4;
}

.sb-row .ic {
  width: 20px;
  font-size: 1.1rem;
}

.sb-emg {
  background: linear-gradient(135deg, #f43f5e 0%, #be123c 100%);
  border: none;
  color: #ffffff !important;
  border-radius: 14px;
  padding: 12px;
  font-weight: 700;
  text-align: center;
  margin-top: 10px;
  font-size: 0.92rem;
  box-shadow: 0 4px 15px rgba(244, 63, 94, 0.3);
  letter-spacing: 0.02em;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  background: rgba(16, 185, 129, 0.1);
  color: #34d399 !important;
  border: 1px solid rgba(16, 185, 129, 0.25);
  padding: 6px 14px;
  border-radius: 999px;
}

.status-pill.demo {
  background: rgba(245, 158, 11, 0.1);
  color: #fbbf24 !important;
  border-color: rgba(245, 158, 11, 0.25);
}

.disclaimer {
  font-size: 0.76rem;
  color: #475569 !important;
  line-height: 1.6;
  margin-top: 10px;
  padding: 0 4px;
}

/* Custom Scrollbar for better UI */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 999px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.25);
}

/* Premium Card Grid Dashboard */
.premium-card-grid {
  margin-top: 15px;
  margin-bottom: 25px;
  display: none; /* Hidden container used as styling anchor */
}

/* Style the columns sibling next to the grid anchor container */
div.element-container:has(.premium-card-grid) + div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] {
  padding: 0 8px !important;
}

/* Style the buttons inside those columns to look like cards */
div.element-container:has(.premium-card-grid) + div[data-testid="stHorizontalBlock"] button {
  height: auto !important;
  min-height: 110px !important;
  border-radius: 20px !important;
  border: 1px solid rgba(255, 255, 255, 0.05) !important;
  background: rgba(30, 41, 59, 0.25) !important;
  color: #94a3b8 !important; /* Muted description color */
  font-size: 0.82rem !important;
  font-weight: 400 !important;
  padding: 18px 20px !important;
  text-align: left !important;
  display: flex !important;
  flex-direction: column !important;
  justify-content: flex-start !important;
  align-items: flex-start !important;
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2) !important;
  backdrop-filter: blur(8px) !important;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
  cursor: pointer !important;
  line-height: 1.5 !important;
  white-space: pre-line !important;
}

/* Make title first-line styled premiumly */
div.element-container:has(.premium-card-grid) + div[data-testid="stHorizontalBlock"] button::first-line {
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-weight: 700 !important;
  font-size: 1.05rem !important;
  color: #ffffff !important;
  line-height: 1.9 !important;
}

div.element-container:has(.premium-card-grid) + div[data-testid="stHorizontalBlock"] button p {
  margin: 0 !important;
  line-height: 1.5 !important;
  text-align: left !important;
}

div.element-container:has(.premium-card-grid) + div[data-testid="stHorizontalBlock"] button:hover {
  border-color: rgba(45, 212, 191, 0.4) !important;
  background: linear-gradient(135deg, rgba(20, 184, 166, 0.08) 0%, rgba(99, 102, 241, 0.08) 100%) !important;
  transform: translateY(-5px) !important;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.4), 0 0 15px rgba(45, 212, 191, 0.15) !important;
}

div.element-container:has(.premium-card-grid) + div[data-testid="stHorizontalBlock"] button:active {
  transform: translateY(-1px) !important;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------
def render_hero() -> None:
    st.html(
        f'<div class="hero"><div class="hero-logo">🩺</div>'
        f'<div class="hero-txt"><h1>{BOT_NAME}</h1>'
        f'<p>{HOSPITAL_NAME} · Patient Help Assistant</p>'
        f'<div class="hero-badges">'
        f'<span class="badge"><span class="dot"></span>Online 24/7</span>'
        f'<span class="badge emg">🚑 Emergency: {EMERGENCY_NUMBER}</span>'
        f'</div></div></div>'
    )


def render_message(role: str, content: str) -> None:
    if role == "assistant":
        body = md_to_html(content)
        st.html(
            f'<div class="msg-row bot"><div class="avatar bot-avatar">🩺</div>'
            f'<div class="bubble bot-bubble">{body}</div></div>'
        )
    else:
        body = html.escape(content).replace("\n", "<br>")
        st.html(
            f'<div class="msg-row user"><div class="avatar user-avatar">🧑</div>'
            f'<div class="bubble user-bubble">{body}</div></div>'
        )


def render_typing() -> None:
    st.html(
        '<div class="msg-row bot"><div class="avatar bot-avatar">🩺</div>'
        '<div class="bubble bot-bubble"><div class="typing"><span></span>'
        '<span></span><span></span></div></div></div>'
    )


def reset_chat() -> None:
    st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE}]


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    reset_chat()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    is_demo = active_provider() == "demo"
    st.html(
        f'<div class="sb-card"><h3>🏥 {HOSPITAL_NAME}</h3>'
        f'<div class="sub">Here to help, day and night.</div>'
        f'<div class="sb-row"><span class="ic">📍</span><span>{ADDRESS}</span></div>'
        f'<div class="sb-row"><span class="ic">☎️</span><span>Helpline: {HELPLINE}</span></div>'
        f'<div class="sb-row"><span class="ic">🕘</span><span>OPD: Mon–Sat, 9 AM – 5 PM</span></div>'
        f'<div class="sb-row"><span class="ic">🌐</span><span>{WEBSITE}</span></div>'
        f'<div class="sb-emg">🚨 Emergency &amp; Ambulance: {EMERGENCY_NUMBER}</div></div>'
    )

    st.html(
        f'<div class="sb-card"><div class="sub" style="margin-bottom:8px">Assistant status</div>'
        f'<span class="status-pill {"demo" if is_demo else ""}">'
        f'{"🟡 Offline demo mode" if is_demo else "🟢 Gemini connected"}</span></div>'
    )
    if is_demo:
        st.caption("Add `GEMINI_API_KEY` to `.env` for full AI replies.")

    if st.button("🗑️  Clear conversation", use_container_width=True):
        reset_chat()
        st.rerun()

    st.html(
        '<div class="disclaimer">⚠️ <b>Not medical advice.</b> MediBot shares general '
        'hospital information only and cannot diagnose or prescribe. In an emergency, '
        'call your local emergency number immediately.</div>'
    )

# ---------------------------------------------------------------------------
# Main: header + chat thread
# ---------------------------------------------------------------------------
render_hero()

for m in st.session_state.messages:
    render_message(m["role"], m["content"])

# If the last turn is the user's, generate the assistant's reply now.
msgs = st.session_state.messages
if msgs and msgs[-1]["role"] == "user":
    render_typing()
    try:
        reply = generate_reply(msgs)
    except LLMError as exc:
        reply = (
            "⚠️ I couldn't reach the assistant just now "
            f"({exc}). Please try again in a moment — or resend your question and I'll retry."
        )
    except Exception as exc:  # noqa: BLE001 - last-resort guard
        reply = f"⚠️ Something went wrong: {exc}. Please try again."
    msgs.append({"role": "assistant", "content": reply})
    st.rerun()

# ---------------------------------------------------------------------------
# Quick-question chips (only at the start of a conversation)
# ---------------------------------------------------------------------------
if len(st.session_state.messages) <= 1:
    st.html('<div class="chips-label">💬 How can we help you today?</div>')
    
    SUGGESTED_CARDS = [
        {
            "title": "📅 Book Appointment",
            "desc": "Consult a doctor & schedule your slot",
            "query": "How do I book an appointment?"
        },
        {
            "title": "🕘 OPD & Visit Timings",
            "desc": "Check patient visiting & clinic hours",
            "query": "What are the OPD and visiting timings?"
        },
        {
            "title": "🩺 Medical Specialities",
            "desc": "View list of departments & clinics",
            "query": "Which departments are available?"
        },
        {
            "title": "🚑 Emergency & Contacts",
            "desc": "24/7 helpline, location & ambulance lines",
            "query": "What is the emergency helpline number?"
        }
    ]
    
    st.markdown('<div class="premium-card-grid">', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, card in enumerate(SUGGESTED_CARDS):
        btn_text = f"{card['title']}\n{card['desc']}"
        if cols[i % 2].button(btn_text, key=f"card_{i}", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": card["query"]})
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Chat input  (+ empty-input handling)
# ---------------------------------------------------------------------------
typed = st.chat_input("Ask about appointments, timings, departments…")
if typed is not None:
    if typed.strip():
        st.session_state.messages.append({"role": "user", "content": typed})
        st.rerun()
    else:
        st.toast("Please type a message first 🙂")
