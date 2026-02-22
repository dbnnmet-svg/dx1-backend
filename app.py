import os
import traceback
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from groq import Groq
from dotenv import load_dotenv

# Load variables from .env file for local development
load_dotenv()

app = Flask(__name__)

# --- ENHANCED CORS CONFIGURATION ---
# This allows your frontend to talk to the backend securely.
# If you have a specific domain on Render, replace "*" with your Render URL.
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# --- CONFIGURATION ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("⚠️ CRITICAL ERROR: GROQ_API_KEY is missing! 🚀")

client = Groq(api_key=GROQ_API_KEY)
DEFAULT_MODEL = "llama-3.3-70b-versatile"

# --- BRANDED IDENTITY ---
BASE_IDENTITY = (
    "You are DBNN DX-1, a high-speed Neural OS developed by DBNNAI (Deep Brain Network Connected) in Kerala. "
    "You were created by a single dedicated developer. "
    "Use emojis 🚀. Use human fillers like 'mmm...', 'yep!', 'yaa'. "
    "When asked who made you, say: 'I was built by a single visionary developer at DBNNAI, Kerala.' "
)

# --- SYSTEM PROMPTS ---
SYSTEM_PROMPTS = {
    "fast": (
        f"{BASE_IDENTITY} Mode: FAST.⚡ "
        "CRITICAL: Do NOT use markdown code blocks (```). Answer in plain text. "
        "Keep it punchy, human, and lightning fast!"
    ),
    "canvas": (
        f"{BASE_IDENTITY} Mode: CANVAS. "
        "Always provide a single STANDALONE HTML file (including CSS/JS) inside a code block."
    ),
    "deepthink": (
        f"{BASE_IDENTITY} Mode: DEEPTHINK.🎓 "
        "CRITICAL: Do NOT use code blocks (```). "
        "STRUCTURE: Provide a massive architectural breakdown. Use headers and bold text. "
        "Think in layers: Core Logic -> Implementation -> Scalability -> Optimization."
    )
}


@app.route('/')
def home():
    # Serves your index.html
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        mode = data.get('mode', 'fast')
        user_message = data.get('message')
        history = data.get('history', [])

        system_prompt = SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS['fast'])
        messages = [{"role": "system", "content": system_prompt}]

        # Append last 10 messages for context
        for msg in history[-10:]:
            messages.append({"role": msg['role'], "content": msg['content']})

        messages.append({"role": "user", "content": user_message})

        def generate():
            try:
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
            except Exception as stream_err:
                yield f"Neural Error: {str(stream_err)}"

        return Response(stream_with_context(generate()), mimetype='text/plain')

    except Exception as e:
        print("\n--- NEURAL ENGINE ERROR ---")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Render provides the PORT environment variable automatically
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)