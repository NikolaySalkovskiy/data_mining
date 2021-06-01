import json
import time
from pathlib import Path
import requests


class Parse5ka:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
    }

    def __init__(self, start_url, save_path: Path):
        self.start_url   = start_url
        self.save_path = save_path

    def _get_response(self, url):
        while True:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response
            time.sleep(0.5)

    def run(self):
        for product in self._parse(self.start_url):
            file_path = self.save_path.joinpath(f'{product["id"]}.json')
            self._save(product, file_path)

    def _parse(self, url):
        while url:
            response = self._get_response(url)
            data: dict = response.json()
            url = data['next']
            for product in data['results']:
                yield product

    def _save(self, data: dict, file_path: Path):
        file_path.write_text(json.dumps(data, ensure_ascii=False), encoding='UTF-8')


def get_save_path(dir_name: str) -> Path:
    save_path = Path(__file__).parent.joinpath(dir_name)
    if not save_path.exists():
        save_path.mkdir()
    return save_path



class ParseCategories(Parse5ka):
    def __init__(self, categories_url, *args, **kwargs):
        self.categories_url = categories_url
        super().__init__(*args, **kwargs)


    def _get_categories(self):
        response = self._get_response(self.categories_url)
        data = response.json()
        return data


    def run(self):
        for category in self._get_categories():
            category['products'] = []
            params = f'?categories={category["parent_group_code"]}'
            url = f'{self.start_url}{params}'
            category['products'].extend(list(self._parse(url)))
            file_name = f'{category["parent_group_code"]}.json'
            cat_path = self.save_path.joinpath(file_name)
            self._save(category, cat_path)


if __name__ == '__main__':
    url = 'https://5ka.ru/api/v2/special_offers/'
    categories_url = 'https://5ka.ru/api/v2/categories/'
    product_path = get_save_path('products')
    parser = Parse5ka(url, product_path)
    category_parser = ParseCategories(categories_url, url, get_save_path('category_products'))
    category_parser.run()