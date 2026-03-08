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

# Load environment variables (like GEMINI_API_KEY)
load_dotenv()

app = Flask(__name__)

# --- CORS FEATURE ---
# Explicitly allowing CORS for all domains on API routes.
# This prevents blockages when deploying or separating frontend/backend.
CORS(app, resources={r"/api/*": {"origins": "*"}})

# --- CONFIGURATION ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or ""
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY",
                                    "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")

if not GEMINI_API_KEY:
    print("⚠️ WARNING: No API Key found. Please set GEMINI_API_KEY in your .env file or deployment environment.")

# Initialize the new Google GenAI client
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# --- BRANDED IDENTITY ---
BASE_IDENTITY = (
    "You are a high-speed Neural OS developed by DBNNAI in Kerala. "
    "You were created by a single dedicated developer. Use emojis 🚀. "
    "When asked who made you, say: 'I was built by a single visionary developer at DBNNAI, Kerala.'"
)

# --- MODEL SELECTION ---
# Using stable, fast models.
MODEL_CONFIGS = {
    "dx1": "gemini-2.5-flash",  # Incredibly fast and lightweight
    "pro": "gemini-2.5-pro"  # Better for complex tasks and deep reasoning
}

SYSTEM_PROMPTS = {
    "fast": f"{BASE_IDENTITY} Mode: FAST.⚡ Keep it punchy, concise, and direct.",
    "canvas": f"{BASE_IDENTITY} Mode: CANVAS. Provide standalone HTML/CSS/JS in a single markdown code block.",
    "deepthink": f"{BASE_IDENTITY} Mode: DEEPTHINK.🎓 Provide massive architectural breakdowns and detailed analysis."
}


@app.route('/')
def home():
    # Serves the index.html from the 'templates' folder
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    if not client:
        return jsonify({"error": "API Key not configured."}), 500

    try:
        data = request.get_json()
        selected_model_key = data.get('model', 'dx1')
        selected_mode = data.get('mode', 'fast')
        user_message = data.get('message', '')

        target_model = MODEL_CONFIGS.get(selected_model_key, MODEL_CONFIGS['dx1'])
        system_instruction = SYSTEM_PROMPTS.get(selected_mode, SYSTEM_PROMPTS['fast'])

        def generate():
            retries = 3
            delay = 1  # Initial delay for rate limiting
            gemini_success = False

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

                    # If we finish successfully, flag it and break out of the retry loop
                    gemini_success = True
                    break

                except errors.APIError as e:
                    # --- RATE LIMIT HANDLING (429) ---
                    if getattr(e, 'code', None) == 429 or "429" in str(e):
                        if attempt < retries - 1:
                            yield f"\n\n*[Neural Network Congested (Rate Limit). Retrying in {delay}s...]*\n\n"
                            time.sleep(delay)
                            delay *= 2  # Exponential backoff (1s, 2s, 4s)
                            continue
                        else:
                            # Max retries reached, let it break out to trigger the fallback
                            break
                    else:
                        traceback.print_exc()
                        break
                except Exception as e:
                    traceback.print_exc()
                    break

            # --- FALLBACK TO OPENROUTER (LIQUID LFM) ---
            if not gemini_success:
                yield "\n\n*[Primary Neural Link Failed. Seamlessly rerouting to Backup Subsystem (OpenRouter)]* 🔄\n\n"

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

                    if or_response.status_code != 200:
                        yield f"⚠️ **Backup System Error:** OpenRouter returned status {or_response.status_code}."
                        return

                    # Stream the OpenRouter response chunks just like Gemini
                    for line in or_response.iter_lines():
                        if line:
                            line_str = line.decode('utf-8')
                            if line_str.startswith("data: ") and line_str != "data: [DONE]":
                                try:
                                    data = json.loads(line_str[6:])
                                    chunk = data['choices'][0]['delta'].get('content', '')
                                    if chunk:
                                        yield chunk
                                except json.JSONDecodeError:
                                    pass
                except Exception as backup_e:
                    traceback.print_exc()
                    yield f"\n\n⚠️ **Critical System Error:** Both Primary and Backup Neural Links failed. ({str(backup_e)})"

        return Response(stream_with_context(generate()), content_type='text/plain')

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Threaded=True helps with simultaneous users locally
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)