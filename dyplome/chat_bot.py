import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from database import init_db, search_knowledge_base, save_to_db
import requests

# Загружаем переменные из .env
load_dotenv("keys.env")  # Указываем путь, если файл называется иначе
API_KEY = os.getenv("TELEGRAM_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CX = os.getenv("GOOGLE_CX_ID")

# Проверка на наличие API_KEY
if not API_KEY:
    raise ValueError("TELEGRAM_TOKEN не найден. Проверь файл keys.env и путь к нему.")

# Инициализация базы данных
init_db()

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я Telegram-бот. Задай мне любой вопрос.")

def search_internet(query):
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API_KEY}&cx={CX}"
    response = requests.get(url)
    if response.status_code == 200:
        results = response.json()
        if 'items' in results:
            first_item = results['items'][0]
            # Проверяем наличие 'snippet' и возвращаем его
            if 'snippet' in first_item:
                return first_item['snippet']
            # Если нет 'snippet', можно вернуть ссылку на страницу
            elif 'link' in first_item:
                return f"Не удалось извлечь описание, но вот ссылка: {first_item['link']}"
            return "Описание и ссылка не найдены."
        return "Не удалось найти информацию в интернете."
    return "Произошла ошибка при поиске в интернете."



def handle_message(update: Update, context: CallbackContext):
    user_input = update.message.text.strip().lower()

    simple_responses = {
        "привет": "Привет! Чем могу помочь?",
        "кто ты": "Я Telegram-чат-бот.",
        "что ты можешь": "Я могу отвечать на вопросы, искать информацию и обучаться."
    }

    if user_input in simple_responses:
        update.message.reply_text(simple_responses[user_input])
        return

    answer = search_knowledge_base(user_input)
    if answer and "не нашёл" not in answer.lower():
        update.message.reply_text(answer)
    else:
        internet_answer = search_internet(user_input)
        update.message.reply_text(f"🔍 {internet_answer}")
        context.user_data['last_q'] = user_input
        context.user_data['last_a'] = internet_answer
        update.message.reply_text("Хочешь, чтобы я запомнил этот ответ? Напиши: /save")

def save(update: Update, context: CallbackContext):
    question = context.user_data.get('last_q')
    answer = context.user_data.get('last_a')
    if question and answer:
        save_to_db(question, answer)
        update.message.reply_text("✅ Ответ сохранён в базе знаний.")
    else:
        update.message.reply_text("⚠️ Нечего сохранять.")

def main():
    updater = Updater(API_KEY, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("save", save))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    print("🤖 Бот запущен.")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
