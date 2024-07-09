# JoyReactor Telegram Bot

Простой Telegram бот для поиска и отправки изображений с сайта JoyReactor.

## Описание

Этот бот позволяет пользователям отправлять запросы на поиск изображений по ключевому слову и тегам через Telegram. Он парсит сайт JoyReactor и отправляет найденные изображения в чат.

## Установка

1. Установите необходимые зависимости, используя `requirements.txt`:

   ```bash
   pip install -r requirements.txt

2. Создайте файл .env в корневой директории проекта и добавьте в него свой API токен Telegram:
  API_TOKEN=your_telegram_bot_api_token

3. Создайте файл cookies.json в корневой директории проекта и добавьте в него свои куки для авторизации на сайте JoyReactor. Этот файл должен иметь следующую структуру:
  [
    {
        "domain": "joyreactor.cc",
        "expirationDate": 1720801968.280742,
        "hostOnly": true,
        "httpOnly": true,
        "name": "joyreactor_sess4",
        "path": "/",
        "sameSite": null,
        "secure": false,
        "session": false,
        "storeId": null,
        "value": "your_cookie_value_here"
    }
]
Замените "your_cookie_value_here" на ваше актуальное значение куки.

##Использование
1. Запустите бота командой:
  ``bash
  python bot.py
2. Отправьте /start, чтобы начать взаимодействие с ботом. Бот запросит ключевое слово для поиска изображений и теги через запятую.
3. Бот будет искать изображения на сайте JoyReactor в соответствии с вашим запросом и отправлять найденные изображения в чат Telegram.

##Лицензия
Этот проект распространяется под лицензией MIT.


