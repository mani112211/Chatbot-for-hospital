# 🏥 MediBot — Hospital Patient Help Assistant

> **InnoViast · Week 1 — AI Development · Track 03: AI Solutions Engineering**
> Assignment 1: *Intent-Based Conversational Assistant*

MediBot is a focused chatbot that helps **hospital patients and visitors** with general,
non-medical questions — booking appointments, OPD and visiting timings, departments,
services, and emergency information. It has a defined persona, a tight scope, strict
**medical-safety rules** (it never diagnoses or prescribes), and **reliable fallback
behavior** for anything outside that scope. It is powered by the **Google Gemini API**,
with an **offline demo mode** so it always runs — even without a key.

The project ships with **two ready-to-run front-ends** that share one brain:

| Front-end | File | Best for |
|-----------|------|----------|
| **Flask web app** (custom HTML/CSS/JS) | `server.py` + `static/` | A full help-desk page: searchable FAQ directory **+** live chat |
| **Streamlit app** (single-file) | `app.py` | The quickest way to launch a polished chat UI |

Both use the same `knowledge.py` (facts + persona) and `llm.py` (Gemini + fallback),
so behaviour is identical no matter which you demo.

---

## ✨ Features

- **Two clean chat UIs** — a Flask help-desk page with a searchable FAQ accordion and a
  live chat panel, plus a single-file Streamlit chat app. Both have avatars, message
  bubbles, typing indicators, and quick-question chips.
- **Defined persona & scope** — a warm, reassuring front-desk assistant that only handles
  general hospital info (see [`prompts/system_prompt.md`](prompts/system_prompt.md)).
- **Medical-safety guardrails** — never gives a diagnosis, medicine, or dosage; guides symptom
  questions to a doctor and emergencies to the emergency number.
- **Reliable fallback** — out-of-scope questions get a polite redirect instead of a made-up answer.
- **Robust error handling** — empty input, API/connection errors, and out-of-scope queries
  are all handled; the UI never crashes.
- **Runs with or without an API key** — offline **demo mode** answers from a built-in
  knowledge base; add a **Gemini** key and it upgrades automatically. If Gemini errors or
  hits its quota, it *degrades gracefully* back to the offline answer.
- **Quick-start suggestions** — one-click common questions.
- **Secure by default** — the API key is read from an environment variable and never committed.

---

## 🧰 Tech Stack

| Layer            | Choice                                                          |
|------------------|----------------------------------------------------------------|
| Web UI (option A)| **Flask** + **Flask-CORS** serving vanilla **HTML / CSS / JS** |
| Chat UI (option B)| **Streamlit** (`st.chat_input`, custom CSS)                   |
| LLM              | Google **Gemini** API via the `google-genai` SDK               |
| Fallback         | Local keyword knowledge base (no key needed)                   |
| Config / secrets | `python-dotenv` + environment variables                        |
| Language         | Python 3.10+ (tested on 3.12)                                  |

> A full breakdown of *what each technology is, why it was chosen, and exactly how it is
> used* lives in **[`DOCUMENTATION.md`](DOCUMENTATION.md)**.

---

## 📁 Project Structure

```
MediBot-InnoViast/
├── server.py               # Flask app: serves the web UI + /api/info & /api/chat
├── app.py                  # Streamlit chat UI + conversation flow + error handling
├── llm.py                  # Provider resolution: Gemini + offline demo mode + graceful fallback
├── knowledge.py            # Persona, system prompt, hospital facts, offline knowledge base
├── static/                 # Front-end for the Flask app
│   ├── index.html          #   FAQ directory + live chat layout
│   ├── app.js              #   Fetches /api/info, renders FAQs, drives the chat
│   └── style.css           #   Theme & responsive styling
├── prompts/
│   └── system_prompt.md    # Prompt documentation (the deliverable)
├── requirements.txt
├── .env.example            # Copy to .env and add your Gemini key
├── .gitignore              # Ignores .env and secrets
├── .streamlit/config.toml  # Streamlit theme
├── README.md               # You are here
├── DOCUMENTATION.md        # Deep-dive: technologies, how they're used, how it works
├── AI_USAGE.md             # Tools, prompts, improvements, limitations, data ethics
└── DEMO_VIDEO_SCRIPT.md    # Shot-by-shot script for the 1–2 min demo video
```

---

## 🚀 Setup & Run

### 1. Install dependencies
```bash
cd MediBot-InnoViast
pip install -r requirements.txt
```

### 2. (Optional) Add your Gemini API key
Get a **free** key from Google AI Studio: <https://aistudio.google.com/app/apikey>

Copy the example env file and paste your key:
```bash
cp .env.example .env      # Windows: copy .env.example .env
```
```env
# .env
GEMINI_API_KEY=your_real_key_here
```
> **No key? No problem.** MediBot automatically runs in **offline demo mode** and answers
> from its built-in knowledge base — perfect for a quick demo.

### 3. Run — pick one front-end

**Option A — Flask web app** (FAQ directory + live chat):
```bash
python server.py
```
Then open <http://localhost:5000>. (Set a different port with `PORT=8000 python server.py`.)

**Option B — Streamlit chat app:**
```bash
streamlit run app.py
```
Then open the URL Streamlit prints (usually <http://localhost:8501>).

---

## 🏥 Customise for your hospital

Open [`knowledge.py`](knowledge.py) and edit the block at the top — **both front-ends update
automatically** because they read from the same file:
```python
HOSPITAL_NAME    = "CityCare Hospital"
HELPLINE         = "+92-300-0000000"
EMERGENCY_NUMBER = "1122"
ADDRESS          = "123 Health Avenue, ..."
WEBSITE          = "www.citycarehospital.example"
```
You can also edit the departments, timings, and answers in `KNOWLEDGE_BASE`, and the safety
keywords in `MEDICAL_ADVICE_KEYWORDS`.

---

## 💬 Example Conversations

**In scope**
> **You:** How do I book an appointment?
> **MediBot:** Call the helpline, book online, or walk in to reception — with a list of steps.

**Medical-safety guardrail**
> **You:** I have a fever and headache, what medicine should I take?
> **MediBot:** I'm not a doctor and can't suggest medicines — let me help you book an appointment, and if it's urgent please call the emergency number.

**Fallback (out of scope)**
> **You:** Can you write a poem for me?
> **MediBot:** I'm here to help with hospital services — appointments, timings, departments, or emergency info. What do you need?

**Error handling**
> Empty message → a gentle nudge to type a question (Streamlit) / `HTTP 400` from the API (Flask).
> API/connection failure → a friendly message + automatic offline fallback (the app never crashes).

---

## 🔌 API Reference (Flask front-end)

The Flask app also exposes a small JSON API, so the same brain can power any front-end:

| Method | Endpoint     | Body                                              | Returns |
|--------|--------------|---------------------------------------------------|---------|
| `GET`  | `/api/info`  | —                                                 | Hospital details, provider status, and the FAQ list |
| `POST` | `/api/chat`  | `{"history": [{"role":"user","content":"..."}]}`  | `{"reply": "..."}` |

```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"history":[{"role":"user","content":"What are the OPD timings?"}]}'
```

---

## 🌐 Deployment

**Streamlit Community Cloud (free):**
1. Push this folder to a GitHub repo named `MediBot-InnoViast`.
2. Go to <https://share.streamlit.io> → **New app** → pick the repo and `app.py`.
3. In **Advanced settings → Secrets**, add your key (do **not** commit it):
   ```toml
   GEMINI_API_KEY = "your_real_key_here"
   ```
4. Deploy and paste the live link below.

**Flask app** deploys anywhere that runs Python (Render, Railway, a VPS, etc.) — start it
with `python server.py` (or a WSGI server such as `gunicorn server:app`) and set
`GEMINI_API_KEY` as an environment variable.

**🔗 Live preview:** _add your deployment URL_

---

## 🔒 Security

- The Gemini API key is read from an environment variable only — never hard-coded.
- `.env` and `.streamlit/secrets.toml` are git-ignored; only `.env.example` (placeholder) is committed.

---

## ⚠️ Medical Disclaimer

MediBot provides **general hospital information only**. It is **not a medical device** and does
**not** offer diagnosis, treatment, or prescriptions. Always consult a qualified doctor for
medical advice. In an emergency, call your local emergency number immediately.

---

## 📸 Screenshots

_Add 3–5 screenshots here (appointment answer, medical-safety guardrail, fallback, error handling,
and the FAQ directory)._

## 🎬 Demo Video

_Add your 1–2 minute screen recording link here._ A ready-to-follow shot list is in
**[`DEMO_VIDEO_SCRIPT.md`](DEMO_VIDEO_SCRIPT.md)**.

---

*Built for the InnoViast Internship Framework — Build. Improve. Deploy. Present.*
