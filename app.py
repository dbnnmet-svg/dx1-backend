import os
import random
import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from groq import Groq
from dotenv import load_dotenv

# Load local .env file
load_dotenv()

# We specify template_folder="." if your index.html is in the same folder as app.py
# Or leave it default if index.html is in a folder named /templates
app = Flask(__name__, template_folder=".")

CORS(app)

# --- API CONFIGURATIONS ---
# Pulling from environment variables for security
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OR_KEYS_RAW = os.getenv("OR_KEYS", "")
OR_API_KEYS = [key.strip() for key in OR_KEYS_RAW.split(",") if key.strip()]

# Fallback keys (your original keys) only if environment variables aren't set
if not GROQ_API_KEY:
    GROQ_API_KEY = "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"
if not OR_API_KEYS:
    OR_API_KEYS = [
        "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",
        "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"
    ]

groq_client = Groq(api_key=GROQ_API_KEY)

# --- MODEL MAPPING ---
CHAT_MODEL = "llama-3.3-70b-versatile"
VISUAL_MODEL = "stepfun/step-3.5-flash:free"
IDENTITY = "You are DBNN DX-1, a premium AI developed by DBNN AI in Kerala, India."

SYSTEM_PROMPTS = {
    "fast": f"{IDENTITY} Mode: ULTRA-FAST. Answer briefly. Focus on speed.",
    "deep-research": f"{IDENTITY} Mode: RESEARCH. Provide exhaustive analysis.",
    "canvas": f"{IDENTITY} Mode: CANVAS. Output ONLY a complete HTML file with Tailwind CSS.",
    "study": f"{IDENTITY} Mode: STUDY. Create interactive PPT-style HTML presentations."
}

def call_openrouter(messages):
    api_key = random.choice(OR_API_KEYS)
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": VISUAL_MODEL,
                "messages": messages,
                "temperature": 0.4
            },
            timeout=45
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# --- ROUTES ---

@app.route('/')
def serve_index():
    # This renders your HTML UI
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    if not data:
        return jsonify({"error": "Missing request body"}), 400

    mode = data.get('mode', 'fast')
    user_message = data.get('message')
    history = data.get('history', [])

    messages = [{"role": "system", "content": SYSTEM_PROMPTS.get(mode, IDENTITY)}]

    for msg in history[-6:]:
        role = "assistant" if msg.get("role") == "model" else msg.get("role")
        messages.append({"role": role, "content": msg.get("content")})

    messages.append({"role": "user", "content": user_message})

    try:
        if mode in ['canvas', 'study']:
            result = call_openrouter(messages)
            if 'choices' in result:
                ai_response = result['choices'][0]['message']['content']
            else:
                raise Exception(f"OpenRouter Failure: {result}")
        else:
            completion = groq_client.chat.completions.create(
                model=CHAT_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=2048
            )
            ai_response = completion.choices[0].message.content

        return jsonify({"response": ai_response})

    except Exception as e:
        print(f"Deployment Error: {str(e)}")
        return jsonify({"error": "Neural Link Interrupted."}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)