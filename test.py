# This file contains old Groq API test code - now using Hugging Face instead
# Commented out as we've migrated to Sarvam 30B via Hugging Face Inference API

# import os
# import requests

# # Get API key from environment
# API_KEY = os.getenv("GROQ_API_KEY")

# if not API_KEY:
#     print("❌ ERROR: GROQ_API_KEY not set")
#     exit()

# url = "https://api.groq.com/openai/v1/chat/completions"

# headers = {
#     "Authorization": f"Bearer {API_KEY}",
#     "Content-Type": "application/json"
# }

# data = {
#     "model": "llama-3.3-70b-versatile",
#     "messages": [
#         {"role": "user", "content": "Say hello in one sentence"}
#     ]
# }

# try:
#     response = requests.post(url, headers=headers, json=data)

#     print("Status Code:", response.status_code)
#     print("Response:", response.json())

#     result = response.json()

#     if "choices" in result:
#         print("\n✅ API KEY WORKING!")
#         print("Answer:", result["choices"][0]["message"]["content"])
#     else:
#         print("\n❌ API KEY NOT WORKING")
#         print(result)

# except Exception as e:
#     print("❌ ERROR:", e)