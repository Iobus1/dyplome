import os
import aiohttp
from dotenv import load_dotenv

load_dotenv("keys.env")

HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
MODEL_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"

headers = {
    "Authorization": f"Bearer {HUGGINGFACE_TOKEN}",
    "Content-Type": "application/json"
}


async def query_huggingface(prompt: str) -> str:
    """Отправка запроса к LLM модели на Hugging Face"""
    payload = {
        "inputs": prompt,
        "parameters": {
            "temperature": 0.7,
            "max_new_tokens": 512,
            "return_full_text": False
        }
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(MODEL_URL, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return f"⚠️ Ошибка Hugging Face: {error_text}"
                data = await response.json()
                return data[0]["generated_text"]
    except Exception as e:
        return f"⚠️ Ошибка при запросе к Hugging Face: {e}"
