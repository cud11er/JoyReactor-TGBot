import telebot
from dotenv import load_dotenv
import os
from get_image import save_media_from_url, fetch_media_from_joyreactor, clean_filename, load_cookies
import logging
from concurrent.futures import ThreadPoolExecutor

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение токена API бота из переменных окружения
API_TOKEN = os.getenv('API_TOKEN')

# Создание экземпляра бота
bot = telebot.TeleBot(API_TOKEN)

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Экземпляр ThreadPoolExecutor для асинхронной обработки изображений
executor = ThreadPoolExecutor(max_workers=5)

# Глобальные переменные для хранения текущего запроса и тегов пользователя
user_search_query = None
user_tags = []
current_page = 1

# Загрузка куки из файла
cookies = load_cookies('cookies.json')  # Заменил на новое имя файла

# Функция для получения и отправки медиа
def send_media(search_query, tags, chat_id, page):
    try:
        media = fetch_media_from_joyreactor(search_query, tags, cookies, page)

        if not media:
            bot.send_message(chat_id, "Медиа не найдено.")
            return

        for item in media:
            media_url = item['url']
            file_name = clean_filename(media_url.split("/")[-1])
            file_path = os.path.join(os.getcwd(), file_name)
            save_media_from_url(media_url, file_path)  # Сохраняем медиа

            # Проверяем размер файла и отправляем его соответствующим образом
            file_size = os.path.getsize(file_path)
            with open(file_path, 'rb') as file:
                if item['type'] == 'image':
                    if file_size > 10 * 1024 * 1024:  # 10 MB
                        bot.send_document(chat_id, file)
                    else:
                        bot.send_photo(chat_id, file)
                elif item['type'] == 'video':
                    bot.send_video(chat_id, file)

            os.remove(file_path)  # Удаляем медиа после отправки
            logging.info(f"Медиа удалено: {file_path}")

        # Отправка кнопки "Следующая страница"
        markup = telebot.types.InlineKeyboardMarkup()
        next_page_btn = telebot.types.InlineKeyboardButton("Следующая страница", callback_data=f"next_page_{page + 1}")
        markup.add(next_page_btn)
        bot.send_message(chat_id, "Все медиа отправлены! Хотите посмотреть больше?", reply_markup=markup)

    except Exception as e:
        bot.send_message(chat_id, f"Произошла ошибка: {e}")
        logging.error(f"Error in send_media: {e}")

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, ("Привет! Отправь мне ключевое слово для поиска медиа (или оставь пустым) "
                           "и теги через запятую (или оставь пустыми). Формат: ключевое слово, тег1, тег2 и т.д.\n"
                           "Примеры:\n"
                           "'Собака улыбка (Если теги не нужны - просто ключевое слово)'\n"
                           "' , тег1, тег2' (если ключевое слово не нужно - сначала пробел с запятой, потом теги)"))

# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    global user_search_query, user_tags, current_page

    try:
        # Разделение сообщения на ключевое слово и теги
        parts = message.text.split(',')
        user_search_query = parts[0].strip() if parts[0].strip() else ''
        user_tags = [tag.strip() for tag in parts[1:] if tag.strip()] if len(parts) > 1 else []
        current_page = 1

        bot.reply_to(message, "Получил запрос. Ищу медиа...")

        # Вызываем функцию отправки медиа асинхронно
        executor.submit(send_media, user_search_query, user_tags, message.chat.id, current_page)

    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка при обработке запроса: {e}")
        logging.error(f"Error in handle_message: {e}")

# Обработчик callback данных для кнопок
@bot.callback_query_handler(func=lambda call: call.data.startswith('next_page_'))
def handle_next_page_callback(call):
    global user_search_query, user_tags

    try:
        next_page = int(call.data.split('_')[-1])
        bot.send_message(call.message.chat.id, f"Ищу медиа на странице {next_page}...")

        # Вызываем функцию отправки медиа асинхронно
        executor.submit(send_media, user_search_query, user_tags, call.message.chat.id, next_page)

    except Exception as e:
        bot.send_message(call.message.chat.id, f"Произошла ошибка при обработке запроса: {e}")
        logging.error(f"Error in handle_next_page_callback: {e}")

# Запуск бота
bot.infinity_polling()
