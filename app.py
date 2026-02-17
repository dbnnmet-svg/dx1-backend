import os
from flask import Flask, render_template, request, jsonify
from groq import Groq

app = Flask(__name__)

# --- CONFIGURATION ---
# Best Practice: Use environment variables.
# For testing, you can replace os.environ.get(...) with your actual key string.
# e.g., api_key = "gsk_..."
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set. Please set it as an environment variable or hardcode it for testing.")

client = Groq(api_key=GROQ_API_KEY)

# Use a model supported by Groq (e.g., llama3-8b, mixtral-8x7b, or llama-3.3-70b-versatile)
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
    # Flask looks for this file in a folder named 'templates'
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        mode = data.get('mode', 'fast')
        user_message = data.get('message')
        history = data.get('history', [])

        # Construct messages
        system_prompt = SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS['fast'])
        messages = [{"role": "system", "content": system_prompt}]

        # Add last 6 messages for context
        for msg in history[-6:]:
            messages.append({"role": msg['role'], "content": msg['content']})

        messages.append({"role": "user", "content": user_message})

        # Call Groq API
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
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)