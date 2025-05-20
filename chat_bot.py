import os
import aiohttp
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from database import (
    init_db,
    search_knowledge_base,
    save_to_db,
    FREQUENT_QUESTIONS,
)

load_dotenv("keys.env")

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ Переменная TELEGRAM_TOKEN не найдена в keys.env")
if not HF_TOKEN:
    raise ValueError("❌ Переменная HUGGINGFACE_TOKEN не найдена в keys.env")

HF_MODEL_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"
HF_HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json",
}

LEARNING_COMMANDS = [
    ["📚 Найти материал", "🧠 Запомнить"],
    ["🔍 Повторить", "❓ Помощь"],
    ["⬅️ В меню"],
]

# Шаблонные ответы
TEMPLATES = {
    "привет": "Привет! Чем могу помочь?",
    "здравствуй": "Здравствуйте! Чем могу помочь?",
    "добрый день": "Добрый день! Какой у вас вопрос?",
    "да": "Отлично!",
    "нет": "Понятно.",
    "пока": "До скорого! Хорошего дня!",
    "спасибо": "Пожалуйста!",
    "приветствую": "Приветствую!",
    "как дела": "У меня всё хорошо, спасибо! Чем могу помочь?",
}

HELP_TEXT = (
    "🆘 <b>Помощь по боту</b>:\n\n"
    "📚 Нажмите <b>«Найти материал»</b>, чтобы задать тему и получить информацию.\n"
    "🧠 После ответа ИИ можно сохранить информацию в вашу базу знаний кнопкой <b>«Запомнить»</b>.\n"
    "🔍 <b>Повторить</b> — повторить последний сохранённый материал.\n"
    "❓ <b>Помощь</b> — показать это сообщение.\n"
    "⬅️ <b>В меню</b> — вернуться в главное меню.\n\n"
    "Если хотите задать вопрос — просто напишите его."
)

async def query_llm(prompt: str, max_tokens: int = 150) -> str:
    """Отправляет запрос к модели Mistral-7B-Instruct на Hugging Face."""
    payload = {
        "inputs": prompt,
        "parameters": {
            "temperature": 0.5,
            "max_new_tokens": max_tokens,
            "return_full_text": False,
        },
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                HF_MODEL_URL, headers=HF_HEADERS, json=payload, timeout=90
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    return f"⚠️ Ошибка Hugging Face API: {error_text}"

                data = await resp.json()
                return data[0]["generated_text"].strip()
    except Exception as e:
        return f"⚠️ Ошибка при обращении к LLM: {e}"

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start — приветствие и меню."""
    await update.message.reply_text(
        "<b>🤖 Учебный помощник 2025</b>\n\n"
        "Задайте мне вопрос по учебной теме, или выберите действие из меню.",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(LEARNING_COMMANDS, resize_keyboard=True),
    )
    context.user_data.clear()

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()

    # Обработка кнопки "В меню"
    if text == "⬅️ В меню":
        await cmd_start(update, context)
        return

    # Обработка кнопки "Помощь"
    if text == "❓ Помощь":
        await update.message.reply_text(HELP_TEXT, parse_mode="HTML")
        return

    # Если ожидаем тему для поиска материала
    if context.user_data.get("awaiting_topic"):
        context.user_data.pop("awaiting_topic")
        topic = text

        # Поиск в локальной базе
        local_answer = search_knowledge_base(topic)
        if local_answer:
            await update.message.reply_text(
                f"📘 <b>Ответ из базы знаний:</b>\n\n{local_answer}", parse_mode="HTML"
            )
            context.user_data["last_response"] = (topic, local_answer)
            return

        await update.message.reply_text("⌛ Пожалуйста, подождите, я ищу ответ...")

        # Формируем чёткий запрос к модели
        llm_prompt = f"Поясни простыми словами разделы математики и их применение на практике по теме: \"{topic}\"."

        llm_answer = await query_llm(llm_prompt)

        # Очищаем начало ответа от лишних символов
        llm_answer = llm_answer.lstrip(",. \n")

        await update.message.reply_text(
            f"🧠 <b>Ответ ИИ:</b>\n\n{llm_answer}",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(
                [["🧠 Запомнить", "⬅️ В меню"]], resize_keyboard=True, one_time_keyboard=True
            ),
        )
        context.user_data["last_response"] = (topic, llm_answer)
        return

    # Обработка шаблонных ответов
    if text.lower() in TEMPLATES:
        await update.message.reply_text(TEMPLATES[text.lower()])
        return

    # Обработка частых вопросов из базы
    for key, answer in FREQUENT_QUESTIONS.items():
        if key in text.lower():
            await update.message.reply_text(
                f"📘 <b>Ответ из базы знаний:</b>\n\n{answer}", parse_mode="HTML"
            )
            return

    # Обработка кнопки "Найти материал" — переходим к вопросу о теме
    if text == "📚 Найти материал":
        context.user_data["awaiting_topic"] = True
        await update.message.reply_text("Введите тему для поиска материала:")
        return

    # Если пустой или непонятный текст
    if not text:
        await update.message.reply_text(
            "⚠️ Я не увидел вопроса. Попробуйте сформулировать запрос конкретнее."
        )
        return

    # Поиск в локальной базе
    local_answer = search_knowledge_base(text)
    if local_answer:
        await update.message.reply_text(
            f"📘 <b>Ответ из базы знаний:</b>\n\n{local_answer}", parse_mode="HTML"
        )
        return

    # Сообщаем о начале поиска
    await update.message.reply_text("⌛ Пожалуйста, подождите, я ищу ответ...")

    llm_prompt = f"Поясни понятным языком для студента: {text}"

    llm_answer = await query_llm(llm_prompt)
    llm_answer = llm_answer.lstrip(",. \n")

    await update.message.reply_text(
        f"🧠 <b>Ответ ИИ:</b>\n\n{llm_answer}",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            [["🧠 Запомнить", "⬅️ В меню"]], resize_keyboard=True, one_time_keyboard=True
        ),
    )
    context.user_data["last_response"] = (text, llm_answer)

async def save_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "last_response" not in context.user_data:
        await update.message.reply_text("❌ Нет информации для сохранения.")
        return

    question, answer = context.user_data["last_response"]
    try:
        save_to_db(question, answer)
        await update.message.reply_text("✅ Сохранено в базе знаний!",
                                        reply_markup=ReplyKeyboardMarkup(LEARNING_COMMANDS, resize_keyboard=True))
    except Exception as e:
        await update.message.reply_text(f"⚠️ Не удалось сохранить: {e}")

def main() -> None:
    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.Regex("^🧠 Запомнить$"), save_response))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("✅ Учебный бот запущен. Ожидаем сообщения...")
    app.run_polling()

if __name__ == "__main__":
    main()
