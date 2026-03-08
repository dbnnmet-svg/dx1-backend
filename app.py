import os
import time
import traceback
import requests
import json
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from google import genai
from google.genai import errors
from dotenv import load_dotenv

# Load local environment variables for testing
load_dotenv()

app = Flask(__name__)

# --- CORS FEATURE ---
# This allows your frontend to communicate with the backend seamlessly across different domains
CORS(app, resources={r"/api/*": {"origins": "*"}})

# --- CONFIGURATION ---
# These will be pulled from Render's Environment Variables settings
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or ""
OPENROUTER_API_KEY = os.environ.get(
    "OPENROUTER_API_KEY") or "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"

# Initialize the Google GenAI client
client = None
if GEMINI_API_KEY:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Neural Init Error: {e}")

# --- BRANDED IDENTITY ---
BASE_IDENTITY = (
    "You are a high-speed Neural OS developed by DBNNAI in Kerala. "
    "You were created by a single dedicated developer. Use emojis 🚀. "
    "When asked who made you, say: 'I was built by a single visionary developer at DBNNAI, Kerala.'"
)

# Optimized Model Configs
MODEL_CONFIGS = {
    "dx1": "gemini-2.5-flash",  # Standard - Fast & Lite
    "pro": "gemini-2.5-pro"  # Pro - Advanced Analysis
}

SYSTEM_PROMPTS = {
    "fast": f"{BASE_IDENTITY} Mode: FAST.⚡ Keep it punchy and direct.",
    "canvas": f"{BASE_IDENTITY} Mode: CANVAS. Provide standalone HTML/CSS/JS in a single code block.",
    "deepthink": f"{BASE_IDENTITY} Mode: DEEPTHINK.🎓 Provide massive architectural breakdowns."
}


@app.route('/')
def home():
    # Make sure your index.html is in the 'templates' folder
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        selected_model_key = data.get('model', 'dx1')
        selected_mode = data.get('mode', 'fast')
        user_message = data.get('message', '')

        target_model = MODEL_CONFIGS.get(selected_model_key, MODEL_CONFIGS['dx1'])
        system_instruction = SYSTEM_PROMPTS.get(selected_mode, SYSTEM_PROMPTS['fast'])

        def generate():
            gemini_success = False

            # 1. ATTEMPT PRIMARY LINK (GEMINI)
            if client:
                retries = 2
                delay = 1
                for attempt in range(retries):
                    try:
                        response = client.models.generate_content_stream(
                            model=target_model,
                            contents=user_message,
                            config={
                                'system_instruction': system_instruction,
                                'temperature': 0.7
                            }
                        )

                        for chunk in response:
                            if chunk.text:
                                yield chunk.text

                        gemini_success = True
                        break  # Exit retry loop on success

                    except Exception as e:
                        # Handle Rate Limiting (429)
                        if "429" in str(e) and attempt < retries - 1:
                            time.sleep(delay)
                            delay *= 2
                            continue
                        print(f"Gemini Failure: {str(e)}")
                        break

            # 2. SEAMLESS REROUTE TO BACKUP (OPENROUTER)
            if not gemini_success:
                yield "\n\n*[Primary Neural Link Failed. Rerouting to Backup Subsystem...]* 🔄\n\n"

                try:
                    or_headers = {
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json"
                    }
                    or_payload = {
                        "model": "liquid/lfm-2.5-1.2b-thinking:free",
                        "messages": [
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": user_message}
                        ],
                        "stream": True
                    }

                    or_response = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=or_headers,
                        json=or_payload,
                        stream=True
                    )

                    for line in or_response.iter_lines():
                        if line:
                            line_str = line.decode('utf-8')
                            if line_str.startswith("data: ") and line_str != "data: [DONE]":
                                try:
                                    data = json.loads(line_str[6:])
                                    chunk = data['choices'][0]['delta'].get('content', '')
                                    if chunk:
                                        yield chunk
                                except:
                                    pass
                except Exception as backup_e:
                    yield f"\n\n⚠️ **Neural Link Severed:** All systems offline. ({str(backup_e)})"

        return Response(stream_with_context(generate()), content_type='text/plain')

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Use the port assigned by Render or default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)