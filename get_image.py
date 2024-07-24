import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlencode, unquote
import re
import json

# Загружаем куки из файла
def load_cookies(cookie_file):
    with open(cookie_file, 'r') as f:
        cookies = json.load(f)
    cookie_dict = {}
    for cookie in cookies:
        cookie_dict[cookie['name']] = cookie['value']
    return cookie_dict

# Функция для получения HTML кода страницы по заданному URL с использованием куки
def get_html(url, cookies):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers, cookies=cookies)
    if response.status_code == 200:
        return response.text
    else:
        print(f'Error {response.status_code} occurred.')
        return None

# Функция для сохранения изображения
def save_image_from_url(img_url, file_path):
    try:
        # Скачиваем и сохраняем изображение
        with requests.get(img_url, stream=True) as r:
            r.raise_for_status()
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f'Saved image: {file_path}')
    except Exception as e:
        print(f'Error saving image {img_url}: {e}')

# Функция для очистки имени файла
def clean_filename(filename):
    # Декодируем URL, чтобы получить нормальный текст
    filename = unquote(filename)
    # Удаляем недопустимые символы
    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    return filename

# Функция для парсинга страницы и извлечения ссылок на изображения
def fetch_images_from_joyreactor(search_query, tags, cookies, page=1):
    try:
        # Формируем базовый URL joyreactor для поиска
        if page == 1:
            base_url = 'https://joyreactor.cc/search?'
            params = {
                'q': search_query,
                'tags': ', '.join(tags)
            }
            full_url = base_url + urlencode(params, safe=',')
        else:
            base_url = f'https://joyreactor.cc/search/{search_query}/{page}?'
            params = {
                'tags': ', '.join(tags)
            }
            full_url = base_url + urlencode(params, safe=',')

        print(f'Search URL: {full_url}')

        # Получаем HTML страницы с результатами поиска
        html = get_html(full_url, cookies)
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
                print('No post list found.')
                return None
        else:
            print('HTML content not retrieved.')
            return None
    except Exception as e:
        print(f'Error fetching images: {e}')
        return None


# Основная функция для выполнения скрипта
if __name__ == "__main__":
    search_query = input("Enter search query: ")
    tags = input("Enter tags (comma separated): ").split(',')
    tags = [tag.strip() for tag in tags]

    cookies = load_cookies('cookie.json')
    images = fetch_images_from_joyreactor(search_query, tags, cookies)

    if images:
        for image in images:
            image_url = image['imageUrl']
            file_name = clean_filename(image_url.split("/")[-1])
            file_path = os.path.join(os.getcwd(), file_name)
            save_image_from_url(image_url, file_path)
    else:
        print("No images found.")
