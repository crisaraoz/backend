import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("OPENAI_API_KEY")
print(f"API key found: {'Yes' if api_key else 'No'}")

try:
    # Initialize the client with explicit settings
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.openai.com/v1"
    )
    
    # Basic test request
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ],
        max_tokens=10
    )
    
    print("OpenAI API test successful!")
    print(f"Response: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"Error: {str(e)}") 