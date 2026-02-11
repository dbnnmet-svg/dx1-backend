from flask import Flask, render_template, request, jsonify
from groq import Groq
import requests
import random

app = Flask(__name__)

# --- API Configurations ---
GROQ_API_KEY = "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"
# Load balancing between your two OpenRouter keys
OR_API_KEYS = [
    "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",
    "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"
]

groq_client = Groq(api_key=GROQ_API_KEY)

# --- Model Mapping ---
DEFAULT_MODEL = "llama-3.3-70b-versatile"
SPECIAL_MODEL = "stepfun/step-3.5-flash:free"

IDENTITY = "You are DBNN DX-1, a premium AI developed by DBNN AI in Kerala, India."

SYSTEM_PROMPTS = {
    "fast": (
        f"{IDENTITY} Mode: ULTRA-FAST. Answer briefly. No intros."
    ),
    "deep-research": (
        f"{IDENTITY} Mode: RESEARCH. Provide exhaustive technical analysis."
    ),
    "canvas": (
        f"{IDENTITY} Mode: CANVAS. Senior Frontend Architect. "
        "Output ONLY a complete, standalone, high-performance HTML file using Tailwind CSS. "
        "Include modern animations (GSAP or CSS keyframes)."
    ),
    "study": (
        f"{IDENTITY} Mode: STUDY. Interactive Learning Architect. "
        "Based on user info, create a 'PPT-style' interactive presentation. "
        "REQUIREMENTS: \n"
        "1. Multiple slides with 'Next/Prev' buttons.\n"
        "2. An interactive MCQ section with instant feedback.\n"
        "3. Smooth fade/slide animations using Tailwind/CSS.\n"
        "4. Entirely standalone HTML/JS code block."
    )
}


def call_openrouter(messages):
    """Helper to call OpenRouter with rotated keys for speed."""
    api_key = random.choice(OR_API_KEYS)
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": SPECIAL_MODEL,
            "messages": messages,
            "temperature": 0.3
        }
    )
    return response.json()


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    mode = data.get('mode', 'fast')
    user_message = data.get('message')
    history = data.get('history', [])

    # Prepare Message Structure
    messages = [{"role": "system", "content": SYSTEM_PROMPTS.get(mode, IDENTITY)}]

    # Process history
    for msg in history[-6:]:
        role = "assistant" if msg.get("role") == "model" else msg.get("role")
        messages.append({"role": role, "content": msg.get("content")})

    messages.append({"role": "user", "content": user_message})

    try:
        # Route to OpenRouter for Canvas/Study, otherwise use Groq
        if mode in ['canvas', 'study']:
            result = call_openrouter(messages)
            if 'choices' in result:
                ai_response = result['choices'][0]['message']['content']
            else:
                raise Exception(f"OpenRouter Error: {result}")
        else:
            completion = groq_client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=messages,
                temperature=0.6,
                max_tokens=2048
            )
            ai_response = completion.choices[0].message.content

        return jsonify({"response": ai_response})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": "Neural Link Interrupted. Check API Keys."}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)