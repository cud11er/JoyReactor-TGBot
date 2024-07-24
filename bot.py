import telebot
from telebot import types
from dotenv import load_dotenv
import os
from get_image import save_image_from_url, fetch_images_from_joyreactor, clean_filename, load_cookies
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
cookies = load_cookies('cookies.json')

# Функция для получения и отправки изображений
def send_images(search_query, tags, chat_id, page=1):
    try:
        # Вызываем функцию для парсинга и получения изображений
        images = fetch_images_from_joyreactor(search_query, tags, cookies, page)

        if not images:
            bot.send_message(chat_id, "Изображения не найдены.")
            return

        for image in images:
            image_url = image['imageUrl']
            file_name = clean_filename(image_url.split("/")[-1])
            file_path = os.path.join(os.getcwd(), file_name)
            save_image_from_url(image_url, file_path)  # Сохраняем изображение

            # Проверяем размер файла и отправляем его соответствующим образом
            file_size = os.path.getsize(file_path)
            with open(file_path, 'rb') as file:
                if file_size > 10 * 1024 * 1024:  # 10 MB
                    bot.send_document(chat_id, file)
                else:
                    bot.send_photo(chat_id, file)

            os.remove(file_path)  # Удаляем изображение после отправки
            logging.info(f"Изображение удалено: {file_path}")

        # Кнопки для управления страницами
        markup = types.InlineKeyboardMarkup()
        next_page_button = types.InlineKeyboardButton('Следующая страница', callback_data=f'next_page:{page+1}')
        markup.add(next_page_button)
        bot.send_message(chat_id, "Загрузить больше изображений?", reply_markup=markup)

    except Exception as e:
        bot.send_message(chat_id, f"Произошла ошибка: {e}")
        logging.error(f"Error in send_images: {e}")

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, ("Привет! Отправь мне ключевое слово для поиска изображений (или оставь пустым) "
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

        bot.reply_to(message, "Получил запрос. Ищу изображения...")

        # Вызываем функцию отправки изображений асинхронно
        executor.submit(send_images, user_search_query, user_tags, message.chat.id, current_page)

    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка при обработке запроса: {e}")
        logging.error(f"Error in handle_message: {e}")

# Обработчик нажатий на inline-кнопки
@bot.callback_query_handler(func=lambda call: call.data.startswith('next_page:'))
def handle_pagination(call):
    global current_page
    try:
        current_page = int(call.data.split(':')[1])
        bot.answer_callback_query(call.id, f"Загрузка страницы {current_page}...")
        executor.submit(send_images, user_search_query, user_tags, call.message.chat.id, current_page)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Произошла ошибка при загрузке страницы: {e}")
        logging.error(f"Error in handle_pagination: {e}")

# Запуск бота
bot.infinity_polling()
