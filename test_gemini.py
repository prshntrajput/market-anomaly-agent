from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

load_dotenv()

def test_gemini_connection():
    print("🧪 Testing Gemini API Connection...\n")
    
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",  # ← updated model
            google_api_key=os.getenv("GOOGLE_API_KEY"),
        )
        
        response = llm.invoke("Say 'Hello from Gemini!' in one line.")
        
        print("✅ SUCCESS! Gemini API is working!")
        print("Response:", response.content)
        return True

    except Exception as e:
        print("❌ ERROR:", e)
        return False

if __name__ == "__main__":
    test_gemini_connection()
