import os
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)
print("KEY PRESENT?", bool(os.getenv("OPENAI_API_KEY")))
#"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"
api_key = ""
# (dont hard code ur key lol but idk wha to do for now
#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

client = OpenAI(api_key=api_key)


def call_llm(prompt):
    # basic helper funtion to call openai
    # just returns text back for now

    # removed env var check cause we are hard coding for now
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content



@app.route("/")
def home():
    print("I WORK")
    return "Backend runing!"

# sreya meri jaan call this only for now 


@app.route("/api/llm-test", methods=["POST"])
def llm_test():
    # endpoint the frontend button can hit
    # sreya meri jaan call this
    # frontend sends json like { "prompt": "hi" }

    data = request.get_json() or {}
    prompt = data.get("prompt", "say hello")

    try:
        result = call_llm(prompt)

        return jsonify({
            "ok": True,
            "response": result
        })

    except Exception as e:
        # basic error handeling for now cause eh
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    # debug true so for someone reason it no work otherwise 
    app.run(debug=True)
