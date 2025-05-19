import requests
from bs4 import BeautifulSoup
from database import save_to_db

def scrape_wikipedia():
    """Парсинг статьи из Википедии для чат-бота"""
    url = "https://ru.wikipedia.org/wiki/Искусственный_интеллект"
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Ищем в статье текст, который может быть полезен для базы знаний
        paragraphs = soup.find_all('p')  # Все абзацы

        for para in paragraphs:
            text = para.get_text(strip=True)
            # Пропускаем пустые абзацы
            if text:
                save_to_db("Что такое искусственный интеллект?", text)  # Сохраняем текст
                print(f"Добавлен абзац: {text[:100]}...")  # Выводим начало текста для проверки
    else:
        print(f"Не удалось получить данные с Википедии, статус код: {response.status_code}")

if __name__ == "__main__":
    scrape_wikipedia()
