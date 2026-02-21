from ctypes import cast
from google import genai
from app.extensions import extensions

#basic helper function to make llm call
#just returns text back for now
def call_llm(prompt: str) -> str:
    client = extensions.get_llm_client()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt)

    if not response.text:
        raise ValueError("Empty response from LLM")
    
    return response.text.strip()