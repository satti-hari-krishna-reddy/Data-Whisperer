import os
import google.generativeai as genai
import deepnote_toolkit

deepnote_toolkit.set_integration_env()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
thinking_model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp")
lite = genai.GenerativeModel("gemini-2.0-flash-lite")
model = genai.GenerativeModel("gemini-2.0-flash")


def get_gemini_response(prompt, type):
    try:
        if type == "thinking":
            response = thinking_model.generate_content(prompt)
        elif type == "lite":
            response = lite.generate_content(prompt)
        else:
            response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error: {e}"
