import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

from knowledge import (
    HOSPITAL_NAME,
    HELPLINE,
    EMERGENCY_NUMBER,
    ADDRESS,
    WEBSITE,
    BOT_NAME,
    BOT_TAGLINE,
    KNOWLEDGE_BASE,
)
from llm import generate_reply, active_provider, provider_label, LLMError

load_dotenv()

app = Flask(__name__, static_folder='static')
CORS(app)

# Serve the frontend
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

# API: Get Hospital Info and FAQs
@app.route('/api/info', methods=['GET'])
def get_info():
    faqs = []
    for item in KNOWLEDGE_BASE:
        # Create user-friendly title from first few keywords or specific mapping
        title = item["keywords"][0].title() if item["keywords"] else "FAQ"
        if "appointment" in item["keywords"]:
            title = "How to Book an Appointment"
        elif "opd" in item["keywords"]:
            title = "OPD & Visiting Timings"
        elif "department" in item["keywords"]:
            title = "Departments & Specialities"
        elif "visiting" in item["keywords"]:
            title = "Visiting Hours & Rules"
        elif "emergency" in item["keywords"]:
            title = "Emergency & Ambulance Services"
        elif "pharmacy" in item["keywords"]:
            title = "Pharmacy & Lab Services"
        elif "insurance" in item["keywords"]:
            title = "Billing & Insurance"
        elif "location" in item["keywords"]:
            title = "Location & Contact Info"
        elif "hello" in item["keywords"]:
            continue  # Skip generic greeting in public FAQ list
            
        faqs.append({
            "title": title,
            "answer": item["answer"],
            "keywords": item["keywords"]
        })

    return jsonify({
        "hospital_name": HOSPITAL_NAME,
        "helpline": HELPLINE,
        "emergency_number": EMERGENCY_NUMBER,
        "address": ADDRESS,
        "website": WEBSITE,
        "bot_name": BOT_NAME,
        "bot_tagline": BOT_TAGLINE,
        "provider": provider_label(),
        "is_demo": active_provider() == "demo",
        "faqs": faqs
    })

# API: Chat response
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json or {}
    history = data.get('history', [])
    
    if not history:
        return jsonify({"error": "No chat history provided"}), 400
        
    try:
        reply = generate_reply(history)
        return jsonify({"reply": reply})
    except LLMError as exc:
        return jsonify({"reply": f"⚠️ I couldn't reach the assistant: {str(exc)}"}), 500
    except Exception as exc:
        return jsonify({"reply": f"⚠️ Error: {str(exc)}"}), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    print(f"Starting server on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
