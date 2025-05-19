import sqlite3

def init_db():
    """Инициализация базы данных и добавление стандартных вопросов и ответов"""
    conn = sqlite3.connect('knowledge_base.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS knowledge_base
                 (question TEXT, answer TEXT)''')

    # Добавление популярных вопросов и ответов в базу данных
    questions_and_answers = [
        ("Что такое ИИ?", "ИИ (искусственный интеллект) — это область информатики, которая занимается созданием систем, способных выполнять задачи, которые обычно требуют человеческого интеллекта, например, обучение, восприятие, рассуждения и решение проблем."),
        ("Кто ты?", "Я чат-бот, созданный для помощи в ответах на вопросы."),
        ("Как тебя зовут?", "Я — ваш помощник, не имею имени, но могу помогать в самых разных вопросах."),
        ("Какой твой функционал?", "Я могу отвечать на вопросы, генерировать тексты, помогать с различными задачами, такими как составление расписания, напоминания и многое другое."),
        ("Понял", "Хорошо, обращайтесь"),
        ("Не надо", "Хорошо, если захотите вернуться, то пишите!"),
        ("Нет/Не", "Понял!"),
        ("Что такое искусственный интеллект?", "Искусственный интеллект — это способность машин имитировать человеческие способности, такие как восприятие, мышление и принятие решений."),
    ]
    
    # Вставляем данные в таблицу
    c.executemany("INSERT OR IGNORE INTO knowledge_base (question, answer) VALUES (?, ?)", questions_and_answers)

    conn.commit()
    conn.close()
    print("✅ База данных инициализирована и заполнена вопросами.")

def save_to_db(question, answer):
    """Сохранение данных в базу"""
    try:
        conn = sqlite3.connect('knowledge_base.db')
        c = conn.cursor()
        c.execute("INSERT INTO knowledge_base (question, answer) VALUES (?, ?)", 
                  (question, answer))
        conn.commit()
        print("💾 Данные сохранены в базу.")
    except Exception as e:
        print(f"❌ Ошибка при сохранении: {e}")
    finally:
        conn.close()

def search_knowledge_base(query):
    """Поиск ответа в базе данных по вопросу"""
    conn = sqlite3.connect('knowledge_base.db')
    c = conn.cursor()
    c.execute("SELECT answer FROM knowledge_base WHERE LOWER(question) LIKE LOWER(?)", 
              ('%' + query + '%',))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0]
    return "Извините, я не нашёл ответа на этот вопрос."
