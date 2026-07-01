# AI_USAGE.md

Transparency document for **MediBot** (InnoViast Week 1 assignment).

---

## 1. Tools Used

| Tool | Purpose |
|------|---------|
| **Streamlit** | Chat UI — message thread, input box, send action, sidebar controls. |
| **Google Gemini API** (`google-genai` SDK) | LLM that generates in-scope replies when a key is provided. |
| **python-dotenv** | Loads the API key from a git-ignored `.env` file. |
| **Local knowledge base** | Offline fallback so the bot runs and demos with no API key. |
| **AI coding assistant** | Used to scaffold the project, draft the system prompt, and write docs (reviewed and edited manually). |

---

## 2. Purpose of the Bot

A tightly-scoped **hospital patient-help assistant**. It answers general, non-medical
questions for a hospital — appointments, OPD/visiting timings, departments, services,
billing/insurance, and emergency info — and politely declines anything outside that scope.
Critically, it **never provides medical diagnosis, treatment, or prescriptions**.

---

## 3. Important Prompts

### System prompt (persona + scope + tone + safety + fallback)
The full system prompt lives in [`prompts/system_prompt.md`](prompts/system_prompt.md)
and in `knowledge.py` (`SYSTEM_PROMPT`). Key design choices:

- **Persona:** warm, calm, reassuring hospital front-desk voice.
- **Scope lock:** limited to general hospital information; told *not* to invent facts,
  doctor schedules, or fees it doesn't have.
- **Safety rules (most important):** never diagnose, name medicines, or give dosages;
  route symptom questions to a doctor and emergencies to the emergency number.
- **Fallback rule:** out-of-scope questions get a specific redirect menu, not a guess.

### Example user prompts tested
- "How do I book an appointment?" → in-scope answer with steps.
- "What are the OPD timings?" → structured timings.
- "I have a fever, what medicine should I take?" → **safety** response (see a doctor).
- "Can you write a poem?" → **fallback** / polite decline.
- "" (empty) → empty-input nudge, not added to history.

---

## 4. Manual Improvements

- Grounded the knowledge base in **realistic hospital facts** (timings, departments,
  contacts) that are easy to customise at the top of `knowledge.py`.
- Added a **safety-first layer**: symptom/medicine keywords are caught *before* normal
  matching (offline mode) and are hard-coded into the Gemini system prompt.
- Built a **Gemini + offline demo** design so the app always runs, even without a key —
  improving demo reliability.
- Added **three layers of error handling**: empty input, wrapped Gemini/API errors
  (`LLMError`), and a last-resort catch-all so the UI never crashes.
- Handled Gemini's `resp.text` raising on blocked/empty responses (converted to a clean error).
- Trimmed conversation history sent to the model (`MAX_HISTORY_TURNS`) to control tokens.

---

## 5. Limitations

- Knowledge is limited to the details in `knowledge.py`; it does not know live doctor
  schedules, real-time bed availability, or exact fees.
- Offline demo mode uses simple keyword matching, so unusual phrasing may fall back to the
  redirect message.
- Not connected to any live hospital database, HIS, or appointment system.
- It is **not** a medical tool — by design it refuses clinical questions.
- Gemini replies depend on the chosen model and can still occasionally be imperfect;
  the system prompt reduces but doesn't fully eliminate this.

---

## 6. Data Ethics

- **No secrets in the repo.** The Gemini API key is read from an environment variable;
  `.env` and `secrets.toml` are git-ignored. Only `.env.example` (placeholder) is committed.
- **No personal / health data collected or stored.** Conversations live only in the browser
  session (Streamlit `session_state`) and are cleared on refresh or via "Clear chat".
- **Patient safety first.** The bot is explicitly instructed never to diagnose or prescribe,
  and to escalate emergencies — protecting users from unsafe AI medical advice.
- **Honesty.** It does not pretend to know doctor schedules or fees it hasn't been given.
- **Attribution.** AI assistance was used to scaffold code and docs; all output was
  reviewed and edited by a human before submission.
