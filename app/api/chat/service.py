import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI client with explicit settings to avoid proxy issues
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://api.openai.com/v1"
)

async def generate_chat_response(messages, model="gpt-3.5-turbo"):
    """
    Generate a response using OpenAI's chat API
    
    Args:
        messages: List of message objects (role, content)
        model: OpenAI model to use
    
    Returns:
        str: Generated response
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
        )
        return {
            "status": "success",
            "message": response.choices[0].message.content,
            "tokens": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    except Exception as e:
        error_message = str(e)
        if "quota" in error_message.lower() or "billing" in error_message.lower():
            return {
                "status": "error",
                "message": "OpenAI API quota exceeded. Please check your billing settings."
            }
        else:
            return {
                "status": "error",
                "message": error_message
            }
