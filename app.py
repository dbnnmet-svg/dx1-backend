from flask import Flask, render_template, request, jsonify
from groq import Groq
import requests
import random

app = Flask(__name__)

# --- API Configurations ---
GROQ_API_KEY = "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"

groq_client = Groq(api_key=GROQ_API_KEY)

# --- Model Mapping ---
DEFAULT_MODEL = "llama-3.3-70b-versatile"

IDENTITY = "You are DBNN DX-1, a premium AI developed by DBNN AI in Kerala, India."

SYSTEM_PROMPTS = {
    "fast": (
        f"{IDENTITY} Mode: ULTRA-FAST. Answer briefly. No intros."
    ),
    "deep-research": (
        f"{IDENTITY} Mode: RESEARCH. Provide exhaustive technical analysis."
    ),
    "canvas": (
        f"{IDENTITY} Mode: CANVAS. Senior Full-Stack Architect. "
        "Output ONLY a complete, standalone, high-performance HTML file. "
        "DESIGN REQUIREMENTS: "
        "1. Always use a dark, premium 'Cyberpunk' or 'Minimalist Tech' aesthetic (Dark backgrounds, glow effects). "
        "2. Use Tailwind CSS and GSAP for animations. "
        "3. If the user provides a short or vague prompt (like 'hi'), do NOT show a plain white box. "
        "Instead, generate a beautiful, animated DBNN DX-1 Welcome Dashboard with glassmorphism, "
        "particle effects, and interactive elements to showcase your capabilities."
    )
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    mode = data.get('mode', 'fast')
    user_message = data.get('message')
    history = data.get('history', [])

    messages = [{"role": "system", "content": SYSTEM_PROMPTS.get(mode, IDENTITY)}]

    for msg in history[-6:]:
        role = "assistant" if msg.get("role") == "model" else msg.get("role")
        messages.append({"role": role, "content": msg.get("content")})

    messages.append({"role": "user", "content": user_message})

    try:
        completion = groq_client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            temperature=0.4, # Slightly lower for more consistent styling
            max_tokens=4096
        )
        ai_response = completion.choices[0].message.content
        return jsonify({"response": ai_response})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": "Neural Link Interrupted. Check Groq API Key."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)