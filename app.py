import os
import random
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
from dotenv import load_dotenv

# Load local .env file if it exists
load_dotenv()

app = Flask(__name__)

# --- CORS CONFIGURATION ---
# Allows your frontend (wherever it is hosted) to communicate with this backend
CORS(app)

# --- API CONFIGURATIONS ---
# Note: In production (Render), these should be moved to Environment Variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")

# Rotation for OpenRouter keys to ensure speed and bypass rate limits
OR_API_KEYS = [
    "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",
    "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"
]

groq_client = Groq(api_key=GROQ_API_KEY)

# --- MODEL MAPPING ---
CHAT_MODEL = "llama-3.3-70b-versatile"
VISUAL_MODEL = "stepfun/step-3.5-flash:free" # Used for Canvas and Study

IDENTITY = "You are DBNN DX-1, a premium AI developed by DBNN AI in Kerala, India."

SYSTEM_PROMPTS = {
    "fast": (
        f"{IDENTITY} Mode: ULTRA-FAST. Answer briefly. No intros. Focus on speed."
    ),
    "deep-research": (
        f"{IDENTITY} Mode: RESEARCH. Provide exhaustive technical analysis with citations."
    ),
    "canvas": (
        f"{IDENTITY} Mode: CANVAS. Senior Frontend Architect. "
        "Output ONLY a complete, standalone, high-performance HTML file using Tailwind CSS. "
        "Include glassmorphism and modern CSS animations."
    ),
    "study": (
        f"{IDENTITY} Mode: STUDY. Interactive Learning Architect. "
        "Create a 'PPT-style' interactive presentation in a standalone HTML block. "
        "REQUIREMENTS: \n"
        "1. Pagination: Slides with 'Next' and 'Previous' functionality.\n"
        "2. Quiz: At least 3 interactive MCQs with instant color-coded feedback (Green/Red).\n"
        "3. Animations: Use Tailwind CSS transitions for slide changes.\n"
        "4. Visuals: Use clean cards and progress bars."
    )
}

def call_openrouter(messages):
    """Handles API calls to OpenRouter with key rotation logic."""
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

@app.route('/')
def health_check():
    return "DBNN DX-1 Backend: Online and Operational."

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    if not data:
        return jsonify({"error": "Missing request body"}), 400

    mode = data.get('mode', 'fast')
    user_message = data.get('message')
    history = data.get('history', [])

    # Initialize messages with System Prompt
    messages = [{"role": "system", "content": SYSTEM_PROMPTS.get(mode, IDENTITY)}]

    # Append History (Last 6 rounds to save tokens/context)
    for msg in history[-6:]:
        role = "assistant" if msg.get("role") == "model" else msg.get("role")
        messages.append({"role": role, "content": msg.get("content")})

    messages.append({"role": "user", "content": user_message})

    try:
        # Route logic: Use Step-3.5-Flash for coding tasks, Llama-3.3 for thinking
        if mode in ['canvas', 'study']:
            result = call_openrouter(messages)
            if 'choices' in result:
                ai_response = result['choices'][0]['message']['content']
            else:
                raise Exception(f"OpenRouter API Failure: {result}")
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
        return jsonify({"error": "Neural Link Interrupted. Verify API balance or keys."}), 500

if __name__ == '__main__':
    # PORT is dynamically assigned by Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)