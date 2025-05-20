import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from database import init_db, search_knowledge_base, save_to_db, FREQUENT_QUESTIONS


load_dotenv("keys.env")
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX_ID = os.getenv("GOOGLE_CX_ID")

if not BOT_TOKEN:
    raise ValueError("❌ Токен бота не найден!")

if not GOOGLE_API_KEY or not GOOGLE_CX_ID:
    raise ValueError("❌ Google API ключ или CX ID не найден в keys.env!")

init_db()

LEARNING_COMMANDS = [
    ["📚 Найти материал", "🧠 Запомнить"],
    ["🔍 Повторить", "❓ Помощь"]
]


async def get_educational_info(query: str) -> str:
    """Поиск обучающей информации на проверенных сайтах"""
    allowed_sites = [
        "khanacademy.org", "wikipedia.org", "britannica.com",
        "coursera.org", "edx.org", "nauka.ru",
        "edu.ru", "habr.com", "sparknotes.com"
    ]
    site_filter = " OR ".join([f"site:{site}" for site in allowed_sites])
    full_query = f"{query} {site_filter}"

    url = f"https://www.googleapis.com/customsearch/v1?q={full_query}&key={GOOGLE_API_KEY}&cx={GOOGLE_CX_ID}"

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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 <b>Учебный помощник 2025</b>\n\n"
        "Я помогу найти и сохранить обучающую информацию по различным темам.\n"
        "Примеры запросов:\n"
        "- Что такое машинное обучение?\n"
        "- Как работает нейросеть?\n"
        "- Теорема Пифагора\n\n"
        "Вы можете начать, написав свой вопрос или выбрав команду ниже.",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(LEARNING_COMMANDS, resize_keyboard=True)
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip().lower()

    # Проверка часто задаваемых вопросов из FREQUENT_QUESTIONS
    for key in FREQUENT_QUESTIONS:
        if key in query:
            await update.message.reply_text(
                f"📘 <b>Ответ из базы знаний:</b>\n\n{FREQUENT_QUESTIONS[key]}",
                parse_mode='HTML'
            )
            return

    if not query:
        await update.message.reply_text(
            "⚠️ Пожалуйста, введите обучающий вопрос — я не могу обработать пустой запрос.\n\n"
            "Например, вы можете спросить меня о самых разных вещах, связанных с наукой, технологиями, историей, математикой и многим другим. "
            "Вот несколько примеров вопросов, которые помогут вам начать:\n"
            "• Что такое искусственный интеллект и как он работает?\n"
            "• Как устроена нейронная сеть и где она применяется?\n"
            "• Какие основные теоремы в геометрии стоит знать?\n"
            "• Объясните принцип работы блокчейн-технологий.\n\n"
            "Я постараюсь найти наиболее точную и полезную информацию по вашему запросу. "
            "Если в моей локальной базе данных нет ответа, я выполню поиск по надежным внешним источникам и предоставлю подробный и развернутый ответ, "
            "который поможет вам лучше понять интересующую тему. Пожалуйста, задавайте вопросы максимально конкретно и понятно."
        )
        return

    # Поиск в локальной базе
    answer_from_db = search_knowledge_base(query)
    if answer_from_db and not answer_from_db.lower().startswith("извините"):
        await update.message.reply_text(
            f"📘 <b>Ответ из базы знаний:</b>\n\n{answer_from_db}\n\n"
            "Если вы хотите получить более подробную информацию или расширить тему, пожалуйста, уточните свой вопрос, и я постараюсь помочь вам еще лучше.",
            parse_mode='HTML'
        )
        return

    # Запрос к Google Custom Search для получения информации
    try:
        result = await get_educational_info(query)
        await update.message.reply_text(
            f"🌐 <b>Информация из внешних источников:</b>\n\n{result}\n\n"
            "Если вы хотите сохранить эту информацию в свою базу знаний для быстрого доступа в будущем, просто нажмите кнопку «🧠 Запомнить».",
            parse_mode='HTML',
            reply_markup=ReplyKeyboardMarkup([["🧠 Запомнить"]], one_time_keyboard=True)
        )
        context.user_data['last_response'] = (query, result)
    except Exception as e:
        print(f"❌ Ошибка получения информации: {e}")
        await update.message.reply_text(
            "⚠️ Произошла ошибка при попытке получить информацию из интернета. Попробуйте повторить запрос позднее или переформулируйте вопрос.",
            parse_mode='HTML'
        )


async def save_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'last_response' not in context.user_data:
        await update.message.reply_text("❌ Нечего сохранять.")
        return

    question, answer = context.user_data['last_response']
    try:
        save_to_db(question, answer)
        await update.message.reply_text("✅ Информация сохранена в базе знаний!")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка сохранения: {e}")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^🧠 Запомнить$"), save_response))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Обучающий чат-бот запущен.")
    app.run_polling()


if __name__ == '__main__':
    main()
