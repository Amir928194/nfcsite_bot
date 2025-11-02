import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import sqlite3
from datetime import datetime
import time

# ⚠️ ВАЖНО: ЗАМЕНИТЕ ЭТИ ДАННЫЕ НА РЕАЛЬНЫЕ!
BOT_TOKEN = "7825783356:AAG5zVMn3-J0ErwFMDkChzRZ2cg2Ysn99zY"  # Получите у @BotFather
ADMIN_IDS = [781193231]  # Ваш ID (узнайте у @userinfobot)

# Создаем бота
bot = telebot.TeleBot(BOT_TOKEN)

# Для хранения временных данных пользователей
user_data = {}

def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            first_name TEXT,
            last_name TEXT,
            contact_type TEXT,
            new_value TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")

@bot.message_handler(commands=['start'])
def start_handler(message):
    """Обработчик команды /start"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = KeyboardButton('📝 Изменить данные')
    markup.add(item1)
    
    bot.send_message(
        message.chat.id,
        "👋 Привет! Я бот для изменения данных на NFC визитке.\n\n"
        "Я помогу вам изменить:\n"
        "• Instagram username\n"
        "• Telegram\n" 
        "• Номер телефона\n"
        "• WhatsApp\n\n"
        "Нажмите кнопку ниже чтобы начать:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == '📝 Изменить данные')
def change_data_handler(message):
    """Начало процесса изменения данных"""
    msg = bot.send_message(
        message.chat.id,
        "📝 Для изменения данных мне понадобится немного информации.\n\n"
        "Пожалуйста, введите ваше ИМЯ и ФАМИЛИЮ через пробел:\n"
        "Пример: Иван Иванов",
        reply_markup=ReplyKeyboardRemove()
    )
    bot.register_next_step_handler(msg, process_name_step)

def process_name_step(message):
    """Обработка имени и фамилии"""
    try:
        chat_id = message.chat.id
        text = message.text.strip()
        names = text.split()
        
        if len(names) < 2:
            msg = bot.send_message(chat_id, "❌ Пожалуйста, введите и имя и фамилию через пробел:\nПример: Иван Иванов")
            bot.register_next_step_handler(msg, process_name_step)
            return
        
        user_data[chat_id] = {
            'first_name': names[0],
            'last_name': ' '.join(names[1:])
        }
        
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton('Instagram'))
        markup.add(KeyboardButton('Telegram'))
        markup.add(KeyboardButton('Номер телефона'))
        markup.add(KeyboardButton('WhatsApp'))
        
        msg = bot.send_message(
            chat_id, 
            "✅ Отлично! Теперь выберите, какие данные вы хотите изменить:",
            reply_markup=markup
        )
        bot.register_next_step_handler(msg, process_contact_type_step)
        
    except Exception as e:
        bot.reply_to(message, '❌ Произошла ошибка. Начните заново с /start')
        print(f"Ошибка в process_name_step: {e}")

def process_contact_type_step(message):
    """Обработка выбора типа контакта"""
    try:
        chat_id = message.chat.id
        
        if message.text not in ['Instagram', 'Telegram', 'Номер телефона', 'WhatsApp']:
            msg = bot.send_message(chat_id, "❌ Пожалуйста, выберите вариант из клавиатуры:")
            bot.register_next_step_handler(msg, process_contact_type_step)
            return
        
        user_data[chat_id]['contact_type'] = message.text
        
        # Определяем подсказку в зависимости от типа контакта
        prompts = {
            'Instagram': "Введите новый username Instagram (без @):",
            'Telegram': "Введите новый username Telegram (без @):", 
            'Номер телефона': "Введите новый номер телефона:",
            'WhatsApp': "Введите новый номер WhatsApp:"
        }
        
        prompt = prompts.get(message.text, "Введите новое значение:")
        
        msg = bot.send_message(chat_id, prompt, reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_new_value_step)
        
    except Exception as e:
        bot.reply_to(message, '❌ Произошла ошибка. Начните заново с /start')
        print(f"Ошибка в process_contact_type_step: {e}")

def process_new_value_step(message):
    """Обработка нового значения"""
    try:
        chat_id = message.chat.id
        user_data[chat_id]['new_value'] = message.text
        
        data = user_data[chat_id]
        first_name = data['first_name']
        last_name = data['last_name']
        contact_type = data['contact_type']
        new_value = data['new_value']
        
        confirmation_text = f"""
📋 Пожалуйста, подтвердите ваши данные:

👤 Имя: {first_name} {last_name}
📝 Изменяем: {contact_type}
🆕 Новое значение: {new_value}

Всё верно?"""
        
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton('✅ Да, всё верно'))
        markup.add(KeyboardButton('❌ Нет, изменить заново'))
        
        msg = bot.send_message(chat_id, confirmation_text, reply_markup=markup)
        bot.register_next_step_handler(msg, process_confirmation_step)
        
    except Exception as e:
        bot.reply_to(message, '❌ Произошла ошибка. Начните заново с /start')
        print(f"Ошибка в process_new_value_step: {e}")

def process_confirmation_step(message):
    """Обработка подтверждения и отправка администраторам"""
    try:
        chat_id = message.chat.id
        
        if message.text == '✅ Да, всё верно':
            data = user_data[chat_id]
            first_name = data['first_name']
            last_name = data['last_name']
            contact_type = data['contact_type']
            new_value = data['new_value']
            
            # Сохраняем в базу данных
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''
                INSERT INTO user_requests (user_id, first_name, last_name, contact_type, new_value, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (chat_id, first_name, last_name, contact_type, new_value, timestamp))
            conn.commit()
            conn.close()
            
            # Отправляем уведомление администраторам
            admin_message = f"""
🚨 НОВЫЙ ЗАПРОС НА ИЗМЕНЕНИЕ ДАННЫХ

👤 Пользователь: {first_name} {last_name}
🆔 User ID: {chat_id}
📱 Контакт: {contact_type}
🆕 Новое значение: {new_value}
⏰ Время: {timestamp}

⚠️ Требуется изменение на Taplink!
            """
            
            # Отправляем всем администраторам
            for admin_id in ADMIN_IDS:
                try:
                    bot.send_message(admin_id, admin_message)
                    print(f"✅ Уведомление отправлено администратору {admin_id}")
                except Exception as e:
                    print(f"❌ Ошибка отправки администратору {admin_id}: {e}")
            
            # Сообщение пользователю
            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(KeyboardButton('📝 Изменить данные'))
            
            user_message = f"""
✅ Ваш запрос принят!

👤 {first_name} {last_name}
📝 {contact_type}: {new_value}

📨 Мы уведомили администраторов. Изменения будут внесены в ближайшее время.

Если нужно изменить другие данные, нажмите кнопку ниже.
            """
            
            bot.send_message(chat_id, user_message, reply_markup=markup)
            
            # Очищаем временные данные
            if chat_id in user_data:
                del user_data[chat_id]
            
        else:
            # Начинаем заново
            msg = bot.send_message(
                chat_id,
                "Давайте начнём заново. Введите ваше ИМЯ и ФАМИЛИЮ через пробел:",
                reply_markup=ReplyKeyboardRemove()
            )
            bot.register_next_step_handler(msg, process_name_step)
            
    except Exception as e:
        bot.reply_to(message, '❌ Произошла ошибка. Начните заново с /start')
        print(f"Ошибка в process_confirmation_step: {e}")

@bot.message_handler(commands=['help'])
def help_handler(message):
    """Команда помощи"""
    help_text = """
📖 Справка по боту:

🔹 /start - Начать работу с ботом
🔹 /help - Получить справку

📝 Какие данные можно изменить:
• Instagram username
• Telegram
• Номер телефона  
• WhatsApp

⏰ Время обработки: обычно до 24 часов

📞 По вопросам: свяжитесь с администратором
    """
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(commands=['admin'])
def admin_handler(message):
    """Команда для администраторов"""
    if message.chat.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "❌ У вас нет прав для этой команды.")
        return
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_requests ORDER BY timestamp DESC LIMIT 10')
    requests = cursor.fetchall()
    conn.close()
    
    if not requests:
        bot.send_message(message.chat.id, "✅ Нет запросов в базе данных.")
        return
    
    response = "📋 Последние 10 запросов:\n\n"
    for req in requests:
        response += f"🆔 {req[0]}\n👤 {req[2]} {req[3]}\n📱 {req[4]}: {req[5]}\n⏰ {req[6]}\n━━━━━━━━━━\n"
    
    bot.send_message(message.chat.id, response)

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    """Обработка любых других сообщений"""
    if message.text not in ['📝 Изменить данные']:
        bot.reply_to(message, "Используйте /start для начала работы или /help для справки")

if __name__ == '__main__':
    # Инициализируем базу данных
    init_db()
    
    print("=" * 50)
    print("🤖 NFC Визитка Бот")
    print("=" * 50)
    print("⚠️  ПРОВЕРЬТЕ ЧТО ВЫ ЗАМЕНИЛИ:")
    print(f"   BOT_TOKEN: {BOT_TOKEN}")
    print(f"   ADMIN_IDS: {ADMIN_IDS}")
    print("=" * 50)
    print("Запуск бота...")
    
    try:
        bot.polling(none_stop=True, interval=1)
    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")
        print("Проверьте токен бота и подключение к интернету")

        time.sleep(5)

