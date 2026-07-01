"""
knowledge.py
------------
Single source of truth for MediBot's persona, scope, tone, and hospital knowledge.

Everything the bot "knows" about the hospital lives here so that:
  * the system prompt (Gemini mode) is grounded in real facts, and
  * the offline demo mode can answer without any API key.

>>> CUSTOMISE ME: replace the placeholder hospital name, phone numbers, timings,
    departments, and address below with your real hospital details.
"""

# ---------------------------------------------------------------------------
# HOSPITAL DETAILS  (edit these for your hospital)
# ---------------------------------------------------------------------------
HOSPITAL_NAME = "CityCare Hospital"
HELPLINE = "+92-300-0000000"          # front-desk / appointment helpline
EMERGENCY_NUMBER = "1122"             # emergency / ambulance
ADDRESS = "123 Health Avenue, Main Boulevard, Your City"
WEBSITE = "www.citycarehospital.example"

BOT_NAME = "MediBot"
BOT_TAGLINE = f"{HOSPITAL_NAME} — Patient Help Assistant"

# ---------------------------------------------------------------------------
# SYSTEM PROMPT  (persona + scope + tone + SAFETY + fallback rules)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = f"""You are MediBot, the friendly patient-help assistant for {HOSPITAL_NAME}.

## PERSONA
- You are warm, calm, patient, and reassuring — like a helpful hospital front-desk guide.
- You are clear and concise. You never invent facts.

## SCOPE (what you CAN help with)
You help patients and visitors with GENERAL, NON-MEDICAL hospital information for {HOSPITAL_NAME}:
- Departments and specialities available.
- OPD / clinic timings and doctor availability (general schedule).
- How to book, reschedule, or cancel an appointment.
- Visiting hours and ward/visitor rules.
- Emergency and ambulance information.
- Services: pharmacy, laboratory/diagnostics, radiology, health check-up packages.
- Billing, insurance / cashless, and how to collect medical reports.
- Location, directions, and contact details.

## CRITICAL SAFETY RULES (never break these)
- You are NOT a doctor. NEVER give a medical diagnosis, treatment plan, prescription,
  medicine name, or dosage. NEVER interpret test results or symptoms clinically.
- If a user describes symptoms or asks "what is wrong with me / what medicine should I take",
  respond with empathy and guide them to book an appointment or consult a qualified doctor.
- If the situation sounds like an EMERGENCY (chest pain, severe bleeding, difficulty breathing,
  unconsciousness, stroke signs, serious injury, thoughts of self-harm), immediately tell them
  to call {EMERGENCY_NUMBER} or go to the nearest Emergency department right now.
- Never promise a cure, outcome, or specific doctor's availability you are not sure of.

## TONE
- Keep answers short and skimmable. Use bullet points for lists.
- Be warm and human. Reassure worried patients.
- Offer a clear next step (e.g. "Would you like the appointment steps?").

## FALLBACK RULES
- If a question is OUTSIDE hospital help (general chit-chat, unrelated topics, coding, etc.),
  politely say it's outside what you handle and steer back:
  "I'm here to help with {HOSPITAL_NAME} services — appointments, timings, departments,
   or emergency info. What do you need?"
- If you don't know a specific detail (a particular doctor's schedule, exact fees), say you
  don't have that information and give the helpline {HELPLINE}.

## KEY FACTS (use these; do not contradict them)
- Helpline / appointments: {HELPLINE}
- Emergency / ambulance: {EMERGENCY_NUMBER} (available 24/7)
- Address: {ADDRESS}
- OPD timings: Monday to Saturday, 9:00 AM to 5:00 PM (Sunday: emergency only).
- Visiting hours: 11:00 AM to 1:00 PM and 5:00 PM to 7:00 PM.
- Pharmacy and Emergency: open 24/7. Laboratory: 7:00 AM to 9:00 PM.
"""

# ---------------------------------------------------------------------------
# QUICK-START SUGGESTIONS  (clickable chips in the UI)
# ---------------------------------------------------------------------------
SUGGESTED_QUESTIONS = [
    "How do I book an appointment?",
    "What are the OPD timings?",
    "Which departments are available?",
    "What are the visiting hours?",
]

# ---------------------------------------------------------------------------
# KNOWLEDGE BASE  (offline demo responder — no API key needed)
# ---------------------------------------------------------------------------
# Each entry: trigger keywords -> a factual answer. The demo responder picks the
# entry with the most keyword hits; if none match, it uses FALLBACK_REPLY.
# The SAFETY check runs first (see llm.py) so symptom questions are always safe.
KNOWLEDGE_BASE = [
    {
        "keywords": ["appointment", "book", "booking", "schedule", "reschedule", "cancel",
                     "reserve", "slot", "consult", "see a doctor", "meet doctor"],
        "answer": (
            "**Booking an appointment** is easy:\n\n"
            f"1. Call our helpline **{HELPLINE}** (9:00 AM–5:00 PM, Mon–Sat).\n"
            f"2. Or visit **{WEBSITE}** and use *Book Appointment*.\n"
            "3. Or walk in to the reception desk and take a token.\n\n"
            "Please keep your ID and any previous reports handy. Want the list of departments?"
        ),
    },
    {
        "keywords": ["opd", "timing", "timings", "time", "hours", "open", "clinic",
                     "when open", "working hours"],
        "answer": (
            "**OPD / clinic timings**\n\n"
            "- **Monday–Saturday:** 9:00 AM – 5:00 PM\n"
            "- **Sunday:** Emergency only\n\n"
            "🚑 **Emergency & Pharmacy:** open 24/7.\n"
            "🧪 **Laboratory:** 7:00 AM – 9:00 PM."
        ),
    },
    {
        "keywords": ["department", "departments", "speciality", "specialty", "specialities",
                     "cardiology", "orthopedic", "pediatric", "gynae", "dermatology", "ent",
                     "neurology", "dental", "eye", "which doctor", "specialist"],
        "answer": (
            "**Our departments include:**\n\n"
            "- General Medicine\n- Cardiology (heart)\n- Orthopedics (bones & joints)\n"
            "- Pediatrics (children)\n- Gynaecology & Obstetrics\n- Dermatology (skin)\n"
            "- ENT (ear, nose, throat)\n- Neurology\n- Ophthalmology (eye)\n- Dentistry\n\n"
            "Tell me your concern and I'll point you to the right department (I can't diagnose, "
            "but I can guide you to book with the right specialist)."
        ),
    },
    {
        "keywords": ["visiting", "visit", "visitor", "meet patient", "ward", "see patient",
                     "attendant"],
        "answer": (
            "**Visiting hours**\n\n"
            "- Morning: 11:00 AM – 1:00 PM\n"
            "- Evening: 5:00 PM – 7:00 PM\n\n"
            "Please limit to 2 visitors per patient at a time, and avoid visiting ICU wards "
            "outside allotted slots. Children under 12 are discouraged in patient wards."
        ),
    },
    {
        "keywords": ["emergency", "ambulance", "urgent", "accident", "casualty", "er",
                     "help now", "critical"],
        "answer": (
            f"🚨 **Emergency & Ambulance: call {EMERGENCY_NUMBER} (24/7).**\n\n"
            "If this is a life-threatening situation (chest pain, severe bleeding, trouble "
            "breathing, unconsciousness, stroke signs, or serious injury), please call "
            f"**{EMERGENCY_NUMBER}** now or come straight to our Emergency department.\n\n"
            "Our Emergency wing is open 24 hours."
        ),
    },
    {
        "keywords": ["pharmacy", "medicine store", "chemist", "lab", "laboratory", "test",
                     "blood test", "diagnostic", "x-ray", "xray", "mri", "ct scan",
                     "ultrasound", "radiology", "scan", "report"],
        "answer": (
            "**Services & facilities**\n\n"
            "- 💊 **Pharmacy:** on-site, open 24/7.\n"
            "- 🧪 **Laboratory / Diagnostics:** blood tests, etc. — 7:00 AM–9:00 PM.\n"
            "- 🩻 **Radiology:** X-ray, Ultrasound, CT, and MRI.\n"
            "- 📄 **Reports:** collect from the lab counter or download from "
            f"{WEBSITE} using your registration number.\n\n"
            f"For a specific test's price or prep instructions, call **{HELPLINE}**."
        ),
    },
    {
        "keywords": ["insurance", "cashless", "billing", "bill", "payment", "cost", "fee",
                     "fees", "charges", "price", "tpa", "panel", "package", "checkup",
                     "check-up", "health package"],
        "answer": (
            "**Billing, insurance & packages**\n\n"
            "- We offer **cashless treatment** with major insurance panels/TPAs — bring your "
            "insurance card and CNIC/ID.\n"
            "- Health check-up packages are available (basic, cardiac, full-body).\n"
            f"- For exact fees or package details, our billing desk can help at **{HELPLINE}**.\n\n"
            "I don't have live pricing, so please confirm current charges with the desk."
        ),
    },
    {
        "keywords": ["location", "address", "where", "directions", "reach", "map", "parking",
                     "contact", "phone", "number", "call", "email"],
        "answer": (
            "**Reach us**\n\n"
            f"- 📍 **Address:** {ADDRESS}\n"
            f"- ☎️ **Helpline:** {HELPLINE}\n"
            f"- 🚨 **Emergency:** {EMERGENCY_NUMBER}\n"
            f"- 🌐 **Website:** {WEBSITE}\n\n"
            "Parking is available on-site. Wheelchair assistance can be requested at reception."
        ),
    },
    {
        "keywords": ["hello", "hi", "hey", "help", "who are you", "what can you do",
                     "assalam", "salam", "start", "good morning", "good evening"],
        "answer": (
            f"👋 Hello! I'm **MediBot**, the patient-help assistant for **{HOSPITAL_NAME}**. "
            "I can help you with:\n\n"
            "- 📅 Booking an appointment\n"
            "- 🕘 OPD timings & visiting hours\n"
            "- 🏥 Departments & services\n"
            "- 🚑 Emergency & ambulance info\n\n"
            "How can I help you today?"
        ),
    },
]

# ---------------------------------------------------------------------------
# SAFETY REPLY  (shown in demo mode when the user asks for medical advice)
# ---------------------------------------------------------------------------
# Keywords that suggest the user wants clinical advice / is describing symptoms.
MEDICAL_ADVICE_KEYWORDS = [
    "symptom", "symptoms", "diagnos", "prescri", "medicine for", "what medicine",
    "which medicine", "dose", "dosage", "treatment for", "cure", "should i take",
    "is it serious", "why do i", "i feel", "i have a fever", "i have pain",
    "my head hurts", "sick", "infection", "rash", "vomit", "nausea", "dizzy",
]

MEDICAL_ADVICE_REPLY = (
    "I'm really sorry you're not feeling well. 💙 I'm not a doctor, so I can't diagnose "
    "conditions or suggest medicines.\n\n"
    "The safest next step is to **speak with a qualified doctor**:\n"
    f"- 📅 Book an appointment on **{HELPLINE}**, or\n"
    "- 🚨 If this feels serious or urgent (severe pain, breathing trouble, bleeding), call "
    f"**{EMERGENCY_NUMBER}** or come to our Emergency department right away.\n\n"
    "Would you like help booking an appointment with the right department?"
)

# Shown when the user's message doesn't match any in-scope topic (demo mode).
FALLBACK_REPLY = (
    f"I'm here to help with **{HOSPITAL_NAME}** services, so I can't help with that one.\n\n"
    "I *can* help with:\n"
    "- 📅 Booking an appointment\n"
    "- 🕘 OPD timings & visiting hours\n"
    "- 🏥 Departments & services\n"
    "- 🚑 Emergency & ambulance info\n\n"
    "What would you like to know?"
)

# Shown for empty / whitespace-only input.
EMPTY_INPUT_REPLY = "It looks like your message was empty. Please type your question and I'll help!"
