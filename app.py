import os
import traceback
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from google import genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
# Fix: Get the key from environment variables or a string.
# DO NOT share your real key publicly!
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or ""

if not GEMINI_API_KEY:
    print("⚠️ WARNING: No API Key found.")

# Initialize the Google GenAI client correctly
client = genai.Client(api_key=GEMINI_API_KEY)

# --- BRANDED IDENTITY ---
BASE_IDENTITY = (
    "You are a high-speed Neural OS developed by DBNNAI in Kerala. "
    "You were created by a single dedicated developer. Use emojis 🚀. "
    "When asked who made you, say: 'I was built by a single visionary developer at DBNNAI, Kerala.'"
)

# Model & Mode Logic
# Note: Ensure these model strings are supported by the current SDK
MODEL_CONFIGS = {
    "dx1": "gemini-2.5-flash-lite",
    "pro": "gemini-3.1-flash-lite-preview"
}

SYSTEM_PROMPTS = {
    "fast": f"{BASE_IDENTITY} Mode: FAST.⚡ Keep it punchy and direct.",
    "canvas": f"{BASE_IDENTITY} Mode: CANVAS. Provide standalone HTML/CSS/JS in a single code block.",
    "deepthink": f"{BASE_IDENTITY} Mode: DEEPTHINK.🎓 Provide massive architectural breakdowns."
}

@app.route('/')
def home():
    # Ensure your HTML file is named 'index.html' and sits in a folder named 'templates'
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        selected_model_key = data.get('model', 'dx1')  # Matches 'dx1' or 'pro' from your JS
        selected_mode = data.get('mode', 'fast')
        user_message = data.get('message', '')

        # Select the correct model and System Prompt
        target_model = MODEL_CONFIGS.get(selected_model_key, MODEL_CONFIGS['dx1'])
        system_instruction = SYSTEM_PROMPTS.get(selected_mode, SYSTEM_PROMPTS['fast'])

        def generate():
            try:
                # The newer SDK uses 'config' with a 'system_instruction' field
                response = client.models.generate_content_stream(
                    model=target_model,
                    contents=user_message,
                    config={
                        'system_instruction': system_instruction,
                        'temperature': 0.7
                    }
                )
                for chunk in response:
                    # chunk.text is the standard way to access the stream
                    if chunk.text:
                        yield chunk.text
            except Exception as stream_err:
                traceback.print_exc()
                yield f"⚠️ Neural Sync Error: {str(stream_err)}"

        return Response(stream_with_context(generate()), content_type='text/plain')

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Using threaded=True helps with streaming multiple users
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)