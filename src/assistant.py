import os
from dotenv import load_dotenv
import openai

def ask_chatgpt(messages, model="gpt-3.5-turbo", temperature=0.7):
    load_dotenv()
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()