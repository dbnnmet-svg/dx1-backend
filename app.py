import os
import traceback
import json
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from groq import Groq
from dotenv import load_dotenv  # New import for local development

# Load variables from .env file if it exists
load_dotenv()

app = Flask(__name__)

# --- CORS CONFIGURATION ---
CORS(app, resources={r"/*": {"origins": "*"}})

# --- CONFIGURATION ---
# This will pull from your .env file locally OR from Render's settings online
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("⚠️ CRITICAL ERROR: GROQ_API_KEY is missing! 🚀")
    print("Local: Ensure you have a .env file with GROQ_API_KEY=your_key")
    print("Render: Ensure you added GROQ_API_KEY in the Environment tab.")

client = Groq(api_key=GROQ_API_KEY)
DEFAULT_MODEL = "llama-3.3-70b-versatile"

# --- BRANDED IDENTITY ---
BASE_IDENTITY = (
    "You are DBNN DX-1, a high-speed Neural OS developed by DBNNAI (Deep Brain Network Connected) in Kerala. "
    "You were created by a single dedicated developer, not a group. "
    "Use emojis 🚀. Use human fillers like 'mmm...', 'yep!', 'yaa'. "
    "CRITICAL: Always type a friendly sentence BEFORE and AFTER any code blocks. "
    "When asked who made you, say: 'I was built by a single visionary developer at DBNNAI, Kerala.' "
)

SYSTEM_PROMPTS = {
    "fast": f"{BASE_IDENTITY} Mode: FAST. Keep responses punchy and human! ⚡",
    "canvas": f"{BASE_IDENTITY} Mode: CANVAS. Always provide a single STANDALONE HTML file (including CSS/JS) for any UI requests.",
    "deepthink": f"{BASE_IDENTITY} Mode: DEEPTHINK. Provide deep architectural analysis. 🎓"
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        mode = data.get('mode', 'fast')
        user_message = data.get('message')
        history = data.get('history', [])

        system_prompt = SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS['fast'])
        messages = [{"role": "system", "content": system_prompt}]

        for msg in history[-10:]:
            messages.append({"role": msg['role'], "content": msg['content']})
        messages.append({"role": "user", "content": user_message})

        def generate():
            completion = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=4096,
                stream=True
            )
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        return Response(stream_with_context(generate()), mimetype='text/plain')

    except Exception as e:
        print("\n--- NEURAL ENGINE ERROR ---")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    # debug=False is safer for production/Render
    app.run(debug=False, host='0.0.0.0', port=port)