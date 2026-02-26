import json
from typing import Any, Dict
from app.extensions import extensions


# helper function to make llm call
# just returns text back for now
def call_llm(prompt: str) -> str:
    client = extensions.get_llm_client()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    if not response.text:
        raise ValueError("Empty response from LLM")

    return response.text.strip()

   #makes it returb a json and match a schema made a easy schema for now
def call_llm_json(prompt: str, json_schema: Dict[str, Any]) -> Dict[str, Any]:
   
    client = extensions.get_llm_client()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": json_schema,
        }
    )

    # google-genai usually puts JSON in response.text if mime typy thingy is application/json
    raw = (response.text or "").strip()
    if not raw:
        raise ValueError("Empty JSON response from LLM")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # If anything goes wrong, surface the raw output for debugging
        raise ValueError(f"LLM did not return valid JSON. Raw:\n{raw}")