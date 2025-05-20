import aiohttp
from keys import GOOGLE_API_KEY, CX

async def fetch_edu_data(query: str) -> str:
    """Поиск обучающего материала через Google Custom Search"""
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API_KEY}&cx={CX}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return "❌ Не удалось получить данные."
                data = await response.json()
                for item in data.get("items", []):
                    title = item.get("title")
                    snippet = item.get("snippet")
                    link = item.get("link")
                    if title and snippet and link:
                        return f"<b>{title}</b>\n\n{snippet}\n\n🔗 {link}"
                return "❌ Не найдено подходящей обучающей информации."
    except Exception as e:
        print(f"Ошибка: {e}")
        return "⚠️ Ошибка при запросе данных."

