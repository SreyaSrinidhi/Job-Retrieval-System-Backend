import os
from google import genai
from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv


app = Flask(__name__)
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

#raise error if no Gemini API key
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

#initialize LLM model
client = genai.Client(api_key=gemini_api_key)

#basic helper function to make llm call
#just returns text back for now
def call_llm(prompt: str) -> str:
    # removed env var check cause we are hard coding for now
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt)

    if not response.text:
        raise ValueError("Empty response from LLM")

    return response.text.strip()


@app.route("/")
def home():
    print("I WORK")
    return "Backend runing!"

# sreya meri jaan call this only for now 


#simple endpoint for testing llm calls
#frontend sends JSON in format: {"prompt": "<prompt_text_here>"}
@app.route("/api/llm-test", methods=["POST"])
def llm_test():
    data = request.get_json() or {}
    prompt = data.get("prompt", "say hello")   #TODO - is say hello really a desirable default?

    try:
        result = call_llm(prompt)

        return jsonify({
            "ok": True,
            "response": result
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    # debug true so for someone reason it no work otherwise 
    app.run(debug=True)
