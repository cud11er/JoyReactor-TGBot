import telebot
from dotenv import load_dotenv
import os
from get_image import save_image_from_url, fetch_images_from_joyreactor, clean_filename
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

# Функция для получения и отправки изображений
def send_images(search_query, tags, chat_id):
    try:
        # Вызываем функцию для парсинга и получения изображений
        images = fetch_images_from_joyreactor(search_query, tags)

        if not images:
            bot.send_message(chat_id, "Изображения не найдены.")
            return

        for image in images:
            image_url = image['imageUrl']
            file_name = clean_filename(image_url.split("/")[-1])
            file_path = os.path.join(os.getcwd(), file_name)
            save_image_from_url(image_url, file_path)  # Сохраняем изображение

            # Отправляем изображение пользователю
            with open(file_path, 'rb') as photo:
                bot.send_photo(chat_id, photo)

            os.remove(file_path)  # Удаляем изображение после отправки
            logging.info(f"Изображение удалено: {file_path}")

        # Сообщение пользователю о завершении запроса и предложении сделать новый запрос
        bot.send_message(chat_id, "Все изображения отправлены! Отправьте новый запрос, чтобы продолжить поиск.")

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
    global user_search_query, user_tags

    try:
        # Разделение сообщения на ключевое слово и теги
        parts = message.text.split(',')
        user_search_query = parts[0].strip() if parts[0].strip() else ''
        user_tags = [tag.strip() for tag in parts[1:] if tag.strip()] if len(parts) > 1 else []

        bot.reply_to(message, "Получил запрос. Ищу изображения...")

        # Вызываем функцию отправки изображений асинхронно
        executor.submit(send_images, user_search_query, user_tags, message.chat.id)

    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка при обработке запроса: {e}")
        logging.error(f"Error in handle_message: {e}")

# Запуск бота
bot.infinity_polling()
