# 📘 MediBot — Technical Documentation

This document explains **what technologies MediBot uses, how each one is used, and how the
whole project works end-to-end**. It complements the [`README.md`](README.md) (setup &
features) and [`AI_USAGE.md`](AI_USAGE.md) (AI-tooling transparency).

- **Project:** MediBot — Hospital Patient Help Assistant
- **Assignment:** InnoViast · Week 1 — Intent-Based Conversational Assistant
- **Language:** Python 3.10+ (developed and tested on 3.12)

---

## 1. What MediBot Is (in one paragraph)

MediBot is a **narrow-scope, safety-first hospital front-desk chatbot**. It answers general,
non-medical questions for a hospital (appointments, timings, departments, services, billing,
emergency info) and **politely refuses everything else** — including, critically, any request
for medical diagnosis or medicine. The same "brain" (`knowledge.py` + `llm.py`) is exposed
through **two independent front-ends**: a Flask web page and a Streamlit app.

---

## 2. Technologies Used — and Why

| Technology | Version (`requirements.txt`) | Role in the project | Why it was chosen |
|-----------|------------------------------|---------------------|-------------------|
| **Python** | 3.10+ | Core language for all logic | Simple, batteries-included, first-class Gemini + web-framework support |
| **Google Gemini API** (`google-genai`) | `>=1.0` | The LLM that generates natural in-scope replies | Free tier, strong instruction-following, modern SDK, good at persona + safety adherence |
| **Streamlit** | `>=1.33` | Single-file interactive chat UI (option B) | Fastest path to a polished, stateful chat UI in pure Python — no JS build step |
| **Flask** | `>=3.0` | Web server + JSON API for the custom front-end (option A) | Lightweight, serves static files *and* a clean `/api/*` layer for the HTML/JS UI |
| **Flask-CORS** | `>=4.0` | Enables cross-origin calls to the API | Lets the front-end (or an external client) call `/api/chat` safely |
| **python-dotenv** | `>=1.0` | Loads the API key from a `.env` file into the environment | Keeps secrets out of code and out of git, per the assignment's security rule |
| **markdown** | `>=3.4` | Renders the model's Markdown replies to HTML (Streamlit side) | Bot answers use bold/lists; this makes them display cleanly |
| **HTML / CSS / JS (vanilla)** | — | The Flask front-end (`static/`) | No framework needed; keeps the web UI dependency-free and easy to grade |

> **Design principle:** every technology is either *the brain* (Gemini + knowledge base) or
> *a way to show the brain* (Streamlit / Flask+JS). The brain is written once and reused, so
> the two UIs can never drift apart in behaviour.

---

## 3. How Each Technology Is Used (concretely)

### 3.1 Google Gemini API — `llm.py`
- The key is read **only** from an environment variable (`GEMINI_API_KEY` or `GOOGLE_API_KEY`)
  via `_gemini_api_key()` — never hard-coded.
- A `genai.Client(api_key=...)` is created and `client.models.generate_content(...)` is called with:
  - `model` — `gemini-2.5-flash` by default (override with the `GEMINI_MODEL` env var).
  - `system_instruction=SYSTEM_PROMPT` — the persona, scope, tone, **safety**, and fallback rules.
  - `temperature=0.4` — low, for consistent, on-brand answers.
  - `max_output_tokens=700` — keeps replies short and cost-bounded.
- Chat history is converted to Gemini's format: roles become `"user"` / `"model"` (Gemini
  does not use `"assistant"`), and only the **last `MAX_HISTORY_TURNS` (12)** turns are sent
  to control token usage.
- `resp.text` can raise or be empty if a response is blocked, so it is wrapped in a `try/except`
  and normalised to a clean string.

### 3.2 Offline demo mode — `llm.py` + `knowledge.py`
- If no key is present (or the SDK isn't installed), `active_provider()` returns `"demo"`.
- `_demo_reply()` does **safety-first keyword matching**:
  1. If the message contains any `MEDICAL_ADVICE_KEYWORDS` (e.g. *symptom, dosage, what medicine*),
     it returns `MEDICAL_ADVICE_REPLY` immediately — before anything else.
  2. Otherwise it scores each `KNOWLEDGE_BASE` entry by how many of its keywords appear in the
     message and returns the best match's answer.
  3. If nothing matches, it returns `FALLBACK_REPLY`.
- This guarantees the app **always runs and demos**, even with zero setup.

### 3.3 Graceful degradation (the best of both)
- When Gemini *is* configured but a call fails (network error, `429`/quota, bad model), `llm.py`
  **falls back to the offline answer** and prefixes a small notice, instead of showing an error
  or crashing. Quota errors get a specific "Quota Exceeded" note.

### 3.4 Streamlit front-end — `app.py`
- `st.set_page_config(...)` sets the tab title/icon/layout.
- A large custom **CSS block** (injected with `st.markdown(..., unsafe_allow_html=True)`) restyles
  Streamlit into a modern dark chat theme (hero header, bubbles, typing dots, sidebar cards).
- **State** lives in `st.session_state.messages` — a list of `{role, content}` dicts.
- Flow: render history → if the last message is the user's, show a typing indicator, call
  `generate_reply()`, append the reply, and `st.rerun()`.
- **Error handling** is layered: `LLMError` → friendly retry message; a catch-all `except` →
  last-resort message; empty input → a `st.toast(...)` nudge (never added to history).
- Markdown replies are rendered to HTML with the `markdown` library (with a safe fallback if
  it isn't installed).

### 3.5 Flask front-end — `server.py` + `static/`
- `server.py` serves `static/index.html` at `/` and exposes two JSON endpoints:
  - **`GET /api/info`** — returns hospital details, the current provider/`is_demo` flag, and a
    cleaned-up **FAQ list** built from `KNOWLEDGE_BASE` (each entry given a friendly title).
  - **`POST /api/chat`** — takes `{"history": [...]}`, calls `generate_reply()`, returns
    `{"reply": ...}`. Empty history → `HTTP 400`; `LLMError`/`Exception` → `HTTP 500` with a
    friendly message.
- `static/app.js` (vanilla JS) drives the page: on load it `fetch`es `/api/info` to populate the
  header, info cards, and searchable FAQ accordion; the chat panel keeps a `chatHistory` array,
  shows a typing indicator, `POST`s to `/api/chat`, and renders replies (with a small Markdown-to-HTML
  formatter). Category tabs, live search, suggestion chips, and "clear chat" are all wired here.
- `static/style.css` provides the theme and responsive layout.

### 3.6 Configuration & secrets
- `python-dotenv`'s `load_dotenv()` runs at the top of both `app.py` and `server.py`.
- `.env` (real key) and `.streamlit/secrets.toml` are **git-ignored**; only `.env.example`
  (a placeholder) is committed.

---

## 4. How the Project Works (architecture)

### 4.1 The shared-brain design

```
                 ┌───────────────────────────┐
                 │        knowledge.py        │
                 │  persona · SYSTEM_PROMPT   │
                 │  hospital facts · KB       │
                 │  safety + fallback text    │
                 └─────────────┬─────────────┘
                               │  (imported by)
                 ┌─────────────▼─────────────┐
                 │           llm.py           │
                 │  active_provider()         │
                 │  generate_reply(history)   │
                 │   ├─ Gemini (if key)       │
                 │   └─ offline demo (else)   │
                 └───────┬───────────┬────────┘
                         │           │
          (imported by)  │           │  (imported by)
              ┌──────────▼──┐   ┌────▼───────────────┐
              │  app.py     │   │  server.py (Flask) │
              │ (Streamlit) │   │  /  /api/info      │
              │             │   │     /api/chat      │
              └──────┬──────┘   └─────────┬──────────┘
                     │                    │ serves
              browser (8501)      static/index.html + app.js + style.css
                                          │
                                   browser (5000)
```

Both UIs call the **exact same** `generate_reply(history)`, so a change to the persona, the
knowledge base, or the safety rules instantly affects both — there is a single source of truth.

### 4.2 Request lifecycle — Flask web chat

1. User loads `http://localhost:5000` → Flask serves `static/index.html`.
2. `app.js` calls **`GET /api/info`** → fills header, info cards, and the FAQ accordion.
3. User types a question (or clicks a chip / FAQ) → `app.js` appends it to `chatHistory`,
   shows the typing dots, and **`POST`s `/api/chat`** with the full history.
4. Flask calls `generate_reply(history)` → Gemini (if a key is set) or the offline responder.
5. Flask returns `{"reply": ...}` → `app.js` removes the typing dots and renders the reply.

### 4.3 Request lifecycle — Streamlit chat

1. `streamlit run app.py` starts the server; the browser opens the app.
2. User input is appended to `st.session_state.messages`, then `st.rerun()`.
3. On rerun, if the last message is the user's, `app.py` renders a typing indicator and calls
   `generate_reply(...)`.
4. The reply is appended to state and rendered as a styled bubble.

### 4.4 Reply decision flow (inside `generate_reply`)

```
history ──► trim to last 12 turns
        │
        ├─ provider == "demo"?
        │      └─► safety keywords? ─yes─► MEDICAL_ADVICE_REPLY
        │              │no
        │              └─► best KB keyword match? ─yes─► KB answer
        │                      │no
        │                      └─► FALLBACK_REPLY
        │
        └─ provider == "gemini"
               └─► call Gemini with SYSTEM_PROMPT
                     ├─ success & non-empty ─► model reply
                     ├─ empty response ──────► offline fallback (+ notice)
                     └─ error / quota ───────► offline fallback (+ notice)
```

---

## 5. File-by-File Reference

| File | Responsibility |
|------|----------------|
| `knowledge.py` | **Single source of truth.** Hospital constants, `SYSTEM_PROMPT`, `KNOWLEDGE_BASE`, safety keywords/replies, and fallback text. This is the file you customise for a real hospital. |
| `llm.py` | Provider resolution (`active_provider`, `provider_label`), the offline responder (`_demo_reply`), the Gemini call (`_gemini_reply`), and the public `generate_reply(history)` with graceful fallback. |
| `server.py` | Flask app. Serves the static front-end and the `/api/info` + `/api/chat` JSON endpoints, with HTTP-status error handling. |
| `app.py` | Streamlit app. Custom-CSS chat UI, session state, quick-question chips, and three layers of error handling. |
| `static/index.html` | Layout for the Flask UI: FAQ directory (search + category tabs) on the left, live chat panel on the right, disclaimer footer. |
| `static/app.js` | Front-end logic: loads `/api/info`, renders FAQs, manages chat history, calls `/api/chat`, formats Markdown, wires all interactions. |
| `static/style.css` | Theme and responsive styling for the Flask UI. |
| `prompts/system_prompt.md` | Human-readable documentation of the system prompt and why it's built that way (Week-1 deliverable). |
| `requirements.txt` | Pinned dependency set. |
| `.env.example` | Placeholder env file to copy to `.env`. |
| `.gitignore` | Keeps secrets and caches out of git. |
| `.streamlit/config.toml` | Streamlit theme config. |

---

## 6. The System Prompt (the heart of behaviour)

The full prompt lives in `SYSTEM_PROMPT` (`knowledge.py`) and is documented in
[`prompts/system_prompt.md`](prompts/system_prompt.md). It is organised into five sections that
map directly to the assignment's quality bar:

| Section | Purpose | Quality-bar requirement it satisfies |
|---------|---------|--------------------------------------|
| **PERSONA** | Warm, calm front-desk voice; "never invent facts" | Clean, trustworthy experience |
| **SCOPE** | Enumerates exactly which topics are allowed | Answer within defined scope |
| **CRITICAL SAFETY RULES** | Forbid diagnosis/medicine/dosage; escalate emergencies | Domain-specific patient safety |
| **TONE** | Short, skimmable, bulleted, offer a next step | Usable UX |
| **FALLBACK RULES** | Redirect out-of-scope questions; admit unknowns → give helpline | Guide the user when it can't answer; don't pretend to know |

Hospital facts (helpline, emergency number, address, timings) are **injected** into the prompt
from the constants at the top of `knowledge.py`, so the prompt is always grounded in real data.

---

## 7. Error Handling & Edge Cases

| Case | Streamlit (`app.py`) | Flask (`server.py`) |
|------|----------------------|---------------------|
| **Empty / whitespace input** | `st.toast("Please type a message first")`; not added to history | Client blocks it; empty `history` → `HTTP 400` |
| **Out-of-scope question** | `FALLBACK_REPLY` (demo) or prompt-driven redirect (Gemini) | same |
| **Medical/symptom question** | `MEDICAL_ADVICE_REPLY` (demo) or safety rules (Gemini) | same |
| **Gemini API / network error** | `LLMError` → friendly message; also auto-falls back to offline answer | `HTTP 500` + friendly message; auto offline fallback |
| **Gemini quota (`429`)** | Offline answer + "Quota Exceeded" notice | same |
| **Empty model response** | Offline answer + notice | same |
| **Unexpected exception** | Catch-all `except` → last-resort message (UI never crashes) | `except` → `HTTP 500` |

---

## 8. Configuration Reference

| Env var | Default | Meaning |
|---------|---------|---------|
| `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) | *(none → demo mode)* | Enables live Gemini replies |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Which Gemini model to call |
| `PORT` | `5000` | Port for the Flask app (`server.py`) |

Tunable constants in code: `MAX_HISTORY_TURNS` (12) and Gemini `temperature` (0.4) /
`max_output_tokens` (700) in `llm.py`.

---

## 9. How to Extend

- **Change the hospital:** edit the constants block and `KNOWLEDGE_BASE` in `knowledge.py`.
- **Add a new topic:** add a `{keywords, answer}` entry to `KNOWLEDGE_BASE` (offline mode) — the
  Gemini path picks it up via the grounded facts automatically.
- **Tighten safety:** add phrases to `MEDICAL_ADVICE_KEYWORDS`.
- **Swap the model provider:** `generate_reply(history)` is the single seam — implement a new
  `_provider_reply()` and branch on it in `active_provider()`.
- **Add a new front-end:** import `generate_reply` and `active_provider` and build any UI you like.

---

## 10. Known Limitations

- Knowledge is limited to `knowledge.py`; no live doctor schedules, bed availability, or exact fees.
- Offline demo mode is keyword-based, so unusual phrasing may hit the fallback message.
- Not connected to any hospital HIS / appointment database — it *guides*, it doesn't *transact*.
- By design, it is **not** a medical tool and refuses clinical questions.
- Gemini replies still depend on the model; the system prompt reduces but can't fully eliminate
  imperfect answers.

---

*Built for the InnoViast Internship Framework — Build. Improve. Deploy. Present.*
