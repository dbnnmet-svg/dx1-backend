from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)

# --- OPENROUTER CONFIG ---
# We use the key you provided, but added a fallback for Render environment variables
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "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")
MODEL_NAME = "liquid/lfm-2.5-1.2b-instruct:free"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

@app.route('/')
def home():
    # This looks for index.html inside the /templates folder
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_data = request.json
    user_message = user_data.get("message")

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": user_message}],
            extra_headers={
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "DX-1 Interface",
            }
        )
        bot_reply = response.choices[0].message.content
        return jsonify({"reply": bot_reply})
    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"}), 500

if __name__ == '__main__':
    # Using port from environment for Render compatibility
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)