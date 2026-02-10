import os
import json
import requests
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__)

# --- CORS CONFIGURATION ---
# Enabled for cross-origin requests on Render
CORS(app)

# --- CONFIGURATION ---
# API Keys provided including the new key and rotated existing ones
API_KEYS = [
    "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",
    "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",
    "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"
]
CURRENT_KEY_INDEX = 0

# Model Configuration
REAL_MODEL = "stepfun/step-3.5-flash:free"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def get_next_key():
    """Rotates through the API keys round-robin style."""
    global CURRENT_KEY_INDEX
    if not API_KEYS:
        return None
    key = API_KEYS[CURRENT_KEY_INDEX]
    CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(API_KEYS)
    return key


@app.route('/')
def home():
    """Serves the frontend."""
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    mode = data.get('mode', 'chat')
    history = data.get('history', [])

    system_prompt = "You are DX-1, a helpful AI assistant made by DBNN."
    if mode == 'canvas':
        system_prompt += " Provide code in markdown blocks. For UI, provide a SINGLE HTML file."
    elif mode == 'study':
        system_prompt += " Output strictly in JSON format for slides and quizzes."
    elif mode == 'deep_research':
        system_prompt += " Break down logic into Step 1, Step 2, etc."

    messages = [{"role": "system", "content": system_prompt}]
    # Safety check for history formatting
    formatted_history = []
    for h in history:
        if isinstance(h, dict) and 'role' in h and 'content' in h:
            formatted_history.append({"role": h['role'], "content": h['content']})

    messages.extend(formatted_history[-10:])
    messages.append({"role": "user", "content": user_message})

    current_api_key = get_next_key()
    headers = {
        "Authorization": f"Bearer {current_api_key}",
        "Content-Type": "application/json",
        "X-Title": "DX-1 Ultra"
    }

    payload = {
        "model": REAL_MODEL,
        "messages": messages,
        "stream": True
    }

    def generate():
        try:
            response = requests.post(OPENROUTER_URL, headers=headers, json=payload, stream=True, timeout=60)
            if response.status_code != 200:
                yield f"API Error: {response.status_code} - {response.text}"
                return

            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        if line == 'data: [DONE]':
                            break
                        try:
                            content = json.loads(line[6:])
                            if 'choices' in content and content['choices']:
                                delta = content['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    yield delta['content']
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
        except Exception as e:
            yield f"Stream Error: {str(e)}"

    return Response(stream_with_context(generate()), content_type='text/plain')


if __name__ == '__main__':
    # Render uses the PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    # host='0.0.0.0' is mandatory for cloud access
    app.run(host='0.0.0.0', port=port)# 1. Initialize git in your folder
