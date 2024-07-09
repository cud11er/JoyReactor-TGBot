import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlencode
import logging
import re
import base64

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Функция для получения HTML кода страницы по заданному URL
def get_html(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        logging.error(f'Error {response.status_code} occurred while fetching URL: {url}')
        return None

# Функция для очистки имени файла от недопустимых символов и ограничения длины имени файла
def clean_filename(url):
    # Используем base64 для кодирования имени файла
    base64_filename = base64.urlsafe_b64encode(url.encode()).decode()[:255]
    return re.sub(r'[\\/*?:"<>|]', "_", base64_filename)

# Функция для сохранения изображения
def save_image_from_url(img_url, file_path):
    try:
        # Скачиваем и сохраняем изображение
        with requests.get(img_url, stream=True) as r:
            r.raise_for_status()
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        logging.info(f'Saved image: {file_path}')
    except Exception as e:
        logging.error(f'Error saving image {img_url}: {e}')

# Функция для парсинга страницы и извлечения ссылок на изображения
def fetch_images_from_joyreactor(search_query, tags):
    try:
        # Базовый URL joyreactor для поиска
        base_url = 'https://joyreactor.cc/search?'

        # Формируем параметры запроса
        params = {
            'q': search_query,
            'user': '',
            'tags': ', '.join(tags)
        }

        # Формируем полный URL для запроса
        full_url = base_url + urlencode(params, safe=',')
        logging.info(f'Search URL: {full_url}')

        # Получаем HTML страницы с результатами поиска
        html = get_html(full_url)
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            post_list = soup.find('div', id='post_list')
            if post_list:
                articles = post_list.find_all('div', class_='article post-normal')
                images = []
                for article in articles:
                    post_content = article.find('div', class_='post_content')
                    if post_content:
                        image_container = post_content.find('div', class_='image')
                        if image_container:
                            img_tag = image_container.find('img')
                            if img_tag and img_tag.has_attr('src'):
                                img_url = urljoin('https://joyreactor.cc/', img_tag['src'])
                                images.append({'imageUrl': img_url})
                return images
            else:
                logging.warning('No post list found on the page.')
                return None
        else:
            logging.error('HTML content not retrieved.')
            return None
    except Exception as e:
        logging.error(f'Error fetching images: {e}')
        return None
