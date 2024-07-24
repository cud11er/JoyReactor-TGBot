import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlencode, unquote
import re
import json

def load_cookies(cookie_file):
    with open(cookie_file, 'r') as f:
        cookies = json.load(f)
    cookie_dict = {}
    for cookie in cookies:
        cookie_dict[cookie['name']] = cookie['value']
    return cookie_dict

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

def save_media_from_url(media_url, file_path):
    try:
        response = requests.get(media_url, stream=True)
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            if os.path.exists(file_path):
                print(f'Successfully saved media: {file_path}')
            else:
                print(f'Error: File not saved correctly: {file_path}')
        else:
            print(f'Error {response.status_code} fetching media: {media_url}')
    except Exception as e:
        print(f'Error saving media {media_url}: {e}')

def clean_filename(filename):
    filename = unquote(filename)
    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    return filename

def fetch_media_from_joyreactor(search_query, tags, cookies, page=1):
    try:
        base_url = 'https://joyreactor.cc/search?'
        params = {
            'q': search_query,
            'tags': ', '.join(tags)
        }

        if page > 1:
            params = {
                'tags': ', '.join(tags)
            }
            full_url = f"https://joyreactor.cc/search/{search_query}/{page}?" + urlencode(params, safe=',')
        else:
            full_url = base_url + urlencode(params, safe=',')

        print(f'Search URL: {full_url}')

        html = get_html(full_url, cookies)
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            post_list = soup.find('div', id='post_list')
            if post_list:
                articles = post_list.find_all('div', class_='article post-normal')
                media = []
                for article in articles:
                    post_content = article.find('div', class_='post_content')
                    if post_content:
                        image_container = post_content.find('div', class_='image')
                        if image_container:
                            img_tag = image_container.find('img')
                            if img_tag and img_tag.has_attr('src'):
                                img_url = urljoin('https://joyreactor.cc/', img_tag['src'])
                                media.append({'type': 'image', 'url': img_url})

                            #video_tag = image_container.find('video')
                            #if video_tag:
                            #    sources = video_tag.find_all('source')
                            #    for source in sources:
                            #        if source.has_attr('src'):
                            #            video_url = urljoin('https://joyreactor.cc/', source['src'])
                            #            # Печать для проверки
                            #            print(f'Found video URL: {video_url}')
                            #            media.append({'type': 'video', 'url': video_url})
#
                return media
            else:
                print('No post list found.')
                return None
        else:
            print('HTML content not retrieved.')
            return None
    except Exception as e:
        print(f'Error fetching media: {e}')
        return None
