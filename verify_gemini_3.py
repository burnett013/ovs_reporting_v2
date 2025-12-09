from utils.llm_parser import call_llm
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def test_gemini_3():
    print("Testing Gemini 3 Pro (gemini-3-pro-preview)...")
    try:
        response = call_llm("Hello, are you Gemini 3 Pro?", model_choice="Gemini 3 Pro")
        print(f"Response: {response}")
        if response:
            print("SUCCESS: Gemini 3 Pro is working.")
        else:
            print("FAILURE: Empty response.")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_gemini_3()
