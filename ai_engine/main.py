import time
from groq import Groq
import config

def test_connection():
    print("=== TESTING GROQ LLM CONNECTION ===")
    print(f"Model: {config.GROQ_MODEL}")
    
    # Initialize the native Groq client
    client = Groq(api_key=config.GROQ_API_KEY)

    prompt = "Hello! Please reply with a very brief, one-sentence greeting."
    print(f"\nSending prompt: '{prompt}'...")
    
    start_time = time.time()
    
    try:
        response = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            timeout=30.0 
        )
        
        elapsed_time = time.time() - start_time
        print(f"\n✅ SUCCESS! (Response time: {elapsed_time:.2f} seconds)")
        print("-" * 40)
        print(f"AI Response: {response.choices[0].message.content.strip()}")
        print("-" * 40)
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"\n❌ FAILED after {elapsed_time:.2f} seconds.")
        print(f"Error Details: {str(e)}")

if __name__ == "__main__":
    test_connection()