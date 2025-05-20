import requests
from bs4 import BeautifulSoup
from database import save_to_db

def scrape_wikipedia():
    """Парсинг статьи из Википедии для чат-бота"""
    url = "https://ru.wikipedia.org/wiki/Искусственный_интеллект"
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        paragraphs = soup.find_all('p')  # Все абзацы

        for para in paragraphs:
            text = para.get_text(strip=True)
            if text:
                save_to_db("Что такое искусственный интеллект?", text)  
                print(f"Добавлен абзац: {text[:100]}...")  
    else:
        print(f"Не удалось получить данные с Википедии, статус код: {response.status_code}")

if __name__ == "__main__":
    scrape_wikipedia()
