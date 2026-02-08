from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)

# --- CONFIGURATION ---
# The list of API keys provided for rotation
API_KEYS = [
    "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",
    "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",
    "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",
    "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",
    "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"
]

# Default model requested
DEFAULT_MODEL = "stepfun/step-3.5-flash"


def get_completion_with_retry(messages, model_override=None):
    """
    Attempts to get a completion using the API keys in rotation.
    If a key fails (rate limit, credit expiry), it moves to the next one.
    """
    last_error = None

    # Try each key in the list
    for api_key in API_KEYS:
        try:
            print(f"Using key ending in ...{api_key[-6:]}")
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
            )

            response = client.chat.completions.create(
                model=model_override or DEFAULT_MODEL,
                messages=messages,
                extra_headers={
                    "HTTP-Referer": "http://localhost:5000",
                    "X-Title": "DBNN DX Interface",
                }
            )
            # If successful, return the content immediately
            return response.choices[0].message.content

        except Exception as e:
            print(f"Key failed: {str(e)}")
            last_error = e
            continue  # Try the next key

    # If all keys fail, raise the last error
    raise Exception(f"All API keys failed. Last error: {str(last_error)}")


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    data = request.json

    # 1. Extract Data
    user_messages = data.get("messages", [])  # Expecting list of {role, content}
    selected_model = data.get("model", "F2")  # Frontend model name (F2, 0c, etc.)

    # 2. Map Frontend Model Names to Real Models
    # Using step-3.5-flash for everything as requested, but you can change these
    model_map = {
        'F2': "stepfun/step-3.5-flash",
        '0c v.2': "stepfun/step-3.5-flash",  # Capable of code
        'D-2': "stepfun/step-3.5-flash",  # Capable of reasoning
        'V-1': "stepfun/step-3.5-flash",
        'Study': "stepfun/step-3.5-flash"
    }

    target_model = model_map.get(selected_model, DEFAULT_MODEL)

    # 3. Inject Identity (DBNN)
    # Check if system prompt exists, if not prepend it, if yes append to it
    system_instruction = "You are an AI created by DBNN. You are helpful, fast, and precise."

    # If the first message is system, update it. Otherwise insert it.
    if user_messages and user_messages[0]['role'] == 'system':
        user_messages[0]['content'] += f" {system_instruction}"
    else:
        user_messages.insert(0, {"role": "system", "content": system_instruction})

    try:
        reply = get_completion_with_retry(user_messages, target_model)
        return jsonify({"reply": reply})

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"reply": f"System Error: Unable to connect to DBNN Cloud. Details: {str(e)}"}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)