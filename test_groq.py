from groq import Groq
import os

key = "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"
print(f"Testing Key: {key[:10]}...")

try:
    client = Groq(api_key=key)
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Explain the importance of fast language models",
            }
        ],
        model="llama-3.3-70b-versatile",
    )
    print("Success! Groq API is working.")
except Exception as e:
    print(f"Failed: {e}")
