import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)

# --- CORS CONFIGURATION ---
# This allows your Netlify frontend (on a different domain) to communicate with this Render backend.
CORS(app)

# --- CONFIGURATION ---
# Replace the string below with your actual API key or set it in your Render environment variables.
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set. Please set it as an environment variable.")

client = Groq(api_key=GROQ_API_KEY)

# Using Llama 3.3 70B via Groq for high-speed, high-quality intelligence.
DEFAULT_MODEL = "llama-3.3-70b-versatile"

# --- SYSTEM PROMPTS ---
BASE_IDENTITY = (
    "You are DBNN DX-1. Use emojis 🚀. Use human fillers like 'mmm...', 'yep!', 'yaa', 'hmmm let me see'. "
    "CRITICAL: Always type a friendly sentence BEFORE and AFTER any code blocks. Never send just code."
)

SYSTEM_PROMPTS = {
    "fast": f"{BASE_IDENTITY} Mode: FAST. Keep it snappy but human! ⚡",
    "deep-research": f"{BASE_IDENTITY} Mode: RESEARCH. Detailed but casual conversation. 🧐",
    "canvas": f"{BASE_IDENTITY} Mode: CANVAS. Provide a SINGLE complete HTML block. 🎨",
    "study": f"{BASE_IDENTITY} Mode: STUDY. Explain like a cool teacher. 🎓"
}

@app.route('/')
def home():
    # Serves the index.html from the 'templates' folder.
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        mode = data.get('mode', 'fast')
        user_message = data.get('message')
        history = data.get('history', [])

        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        # Construct messages for the Groq API
        system_prompt = SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS['fast'])
        messages = [{"role": "system", "content": system_prompt}]

        # Append conversation history for context (last 6 messages)
        for msg in history[-6:]:
            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                messages.append({"role": msg['role'], "content": msg['content']})

        messages.append({"role": "user", "content": user_message})

        # Call Groq API for lightning-fast inference
        completion = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
            stream=False
        )

        response_content = completion.choices[0].message.content
        return jsonify({"response": response_content})

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # 'PORT' is automatically provided by Render; defaults to 5000 for local testing.
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)