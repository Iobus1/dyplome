import aiohttp
from keys import GOOGLE_API_KEY, CX

async def fetch_edu_data(query: str) -> str:
    """Поиск обучающего материала только по проверенным образовательным источникам"""
    allowed_sites = [
        "khanacademy.org",
        "wikipedia.org",
        "britannica.com",
        "coursera.org",
        "edx.org",
        "nauka.ru",
        "edu.ru",
        "habr.com",
        "sparknotes.com"
    ]
    site_filter = " OR ".join([f"site:{site}" for site in allowed_sites])
    full_query = f"{query} {site_filter}"

    url = f"https://www.googleapis.com/customsearch/v1?q={full_query}&key={GOOGLE_API_KEY}&cx={CX}"

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
