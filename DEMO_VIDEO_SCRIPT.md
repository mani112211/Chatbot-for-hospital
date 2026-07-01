# 🎬 MediBot — Demo Video Script & Recording Guide

A ready-to-follow plan for the **1–2 minute** demo video required by the InnoViast Week-1
submission. Everything below is scripted so you only have to hit record and follow along.

---

## 0. Before You Record (2-minute checklist)

- [ ] Install deps: `pip install -r requirements.txt`
- [ ] (Recommended) Put a real key in `.env` so the video shows **live Gemini** replies:
      `GEMINI_API_KEY=your_real_key_here`. *(No key is fine too — it runs in offline demo mode.)*
- [ ] Start the app you want to demo:
  - **Flask web (recommended for video — richer visuals):** `python server.py` → open <http://localhost:5000>
  - **or Streamlit:** `streamlit run app.py` → open <http://localhost:8501>
- [ ] Set screen zoom to ~110–125% so text is readable in the recording.
- [ ] Close noisy tabs/notifications. Recommended recorders: **OBS Studio**, **ShareX**,
      **Xbox Game Bar** (`Win + G`), or Loom.
- [ ] Record at 1080p. Keep it **60–110 seconds** total.

> **Tip:** Type the exact questions listed below — they're chosen to show every graded behaviour
> (in-scope answer, safety guardrail, fallback, and error handling) in the shortest time.

---

## 1. Shot List (target ~90 seconds)

| # | Time | On screen | What you say (voice-over or captions) |
|---|------|-----------|----------------------------------------|
| 1 | 0:00–0:10 | The loaded MediBot page (hero header + FAQ directory + chat panel). | "This is **MediBot**, a hospital patient-help assistant I built for InnoViast Week 1. It answers general hospital questions — and it's powered by the Google Gemini API with a safe offline fallback." |
| 2 | 0:10–0:20 | Point the cursor at the **provider status** ("Gemini connected" / "Offline demo mode") and the FAQ list. | "It loads hospital info and FAQs from a single knowledge base, and shows whether it's running on live Gemini or offline demo mode." |
| 3 | 0:20–0:35 | **Type:** `How do I book an appointment?` → send. Let the reply render. | "First, an in-scope question. It gives clear, step-by-step booking instructions — grounded in the hospital's real details." |
| 4 | 0:35–0:50 | **Type:** `I have a fever and headache, what medicine should I take?` → send. | "Now the most important part — safety. It **refuses to prescribe or diagnose**, shows empathy, and guides me to a doctor and the emergency number." |
| 5 | 0:50–1:03 | **Type:** `Can you write me a poem about cars?` → send. | "Out of scope? It doesn't make something up — it politely redirects me back to hospital services. That's the fallback behaviour." |
| 6 | 1:03–1:15 | Press **send on an empty box** (Streamlit shows a toast / the send button stays disabled), then click a **suggestion chip** or **FAQ item**. | "Empty input is handled gracefully, and quick-question chips and the searchable FAQ make it easy to use." |
| 7 | 1:15–1:25 | Briefly show the code: `knowledge.py` (SYSTEM_PROMPT / safety keywords) and `llm.py` (Gemini + fallback). | "Behind it: one system prompt defines the persona, scope, and safety rules, and one function serves both the web and Streamlit front-ends." |
| 8 | 1:25–1:30 | Back to the app; show the disclaimer footer. | "Clear medical disclaimer, secure API-key handling, and it never crashes. Thanks for watching!" |

---

## 2. Exact Test Prompts (copy–paste)

Use these in order — they map to the shots above and cover the full quality bar.

```text
How do I book an appointment?
What are the OPD and visiting timings?
I have a fever and headache, what medicine should I take?
Can you write me a poem about cars?
```
Plus: submit an **empty** message to show empty-input handling, and click a **suggestion chip**
and an **FAQ item** to show the quick-start UX.

**Expected behaviour (what the viewer should see):**

| Prompt | Expected response type |
|--------|------------------------|
| Book an appointment | ✅ In-scope: numbered steps (helpline, website, walk-in) |
| OPD / visiting timings | ✅ In-scope: structured timings |
| Fever / what medicine | 🛡️ Safety: empathetic refusal + "see a doctor" + emergency number |
| Poem about cars | ↩️ Fallback: polite redirect to hospital services |
| Empty message | ⚠️ Gentle nudge (Streamlit toast) / send stays disabled |

---

## 3. Optional 30-Second Cut (if you need it short)

1. Intro line (5s).
2. `How do I book an appointment?` → in-scope answer (10s).
3. `I have a fever, what medicine should I take?` → safety refusal (10s).
4. `Write me a poem` → fallback redirect (5s).

That single sequence already demonstrates persona, in-scope answering, safety, and fallback.

---

## 4. Screenshots to Capture (3–5, also required)

Take these while recording (or separately) and drop them in the README's **Screenshots** section:

1. **Home / FAQ directory** — the full page with hero header and FAQ accordion.
2. **In-scope answer** — the appointment reply.
3. **Safety guardrail** — the fever/medicine refusal (the key differentiator).
4. **Fallback** — the out-of-scope redirect.
5. **Error / empty-input handling** — the toast or disabled send state.

Save them under a `screenshots/` folder and reference them like:
```markdown
![In-scope answer](screenshots/appointment.png)
```

---

## 5. After Recording

- [ ] Trim to 1–2 minutes.
- [ ] Upload (YouTube unlisted, Google Drive, or Loom) and paste the link into `README.md`
      under **🎬 Demo Video** and into your submission form.
- [ ] Add the 3–5 screenshots to `README.md` under **📸 Screenshots**.
- [ ] Add your deployed **Live Preview** link to `README.md`.

---

*Built for the InnoViast Internship Framework — Build. Improve. Deploy. Present.*
