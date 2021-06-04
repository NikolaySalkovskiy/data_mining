import typing
import time
import requests
from urllib.parse import urljoin
import bs4
import pymongo
from database.database import Database


class GbBlogParse:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
    }
    __parse_time = 0

    def __init__(self, start_url, db: Database, delay=1.0):
        self.start_url = start_url
        self.delay = delay
        self.db = db
        self.done_urls = set()
        self.tasks = []
        self.tasks_creator({self.start_url, }, self.parse_feed)

    def _get_response(self, url):
        while True:
            next_time = self.__parse_time + self.delay
            if next_time > time.time():
                time.sleep(next_time - time.time())
            response = requests.get(url, headers=self.headers)
            self.__parse_time = time.time()
            if response.status_code == 200:
                return response

    def get_task(self, url: str, callback: typing.Callable) -> typing.Callable:
        def task():
            response = self._get_response(url)
            return callback(response)
        return task

    def tasks_creator(self, urls: set, callback: typing.Callable):
        urls_set = urls - self.done_urls
        for url in urls_set:
            self.tasks.append(
                self.get_task(url, callback)
            )
            self.done_urls.add(url)

    def run(self):
        while True:
            try:
                task = self.tasks.pop(0)
                task()
            except IndexError:
                break

    def parse_feed(self, response: requests.Response):
        soup = bs4.BeautifulSoup(response.text, 'lxml')
        ul_pagination = soup.find('ul', attrs={'class': 'gb__pagination'})
        pagination_links = set(
            urljoin(response.url, itm.attrs.get('href'))
            for itm in ul_pagination.find_all('a')
            if itm.attrs.get('href')
        )
        self.tasks_creator(pagination_links, self.parse_feed)
        post_wrapper = soup.find('div', attrs={"class": "post-items-wrapper"})
        post_links = set(
            urljoin(response.url, itm.attrs.get('href'))
            for itm in post_wrapper.find_all('a', attrs={"class": "post-item__title"})
            if itm.attrs.get('href')
        )
        self.tasks_creator(post_links, self.parse_post)

    def parse_post(self, response: requests.Response):
        soup = bs4.BeautifulSoup(response.text, 'lxml')
        author_name_tag = soup.find('div', attrs={'itemprop': 'author'})
        data = {
            'post_data': {
                'url': response.url,
                'title': soup.find('h1', attrs={'class': 'blogpost-title'}).text,
                'id': int(soup.find('comments').attrs.get('commentable-id'))
            },
            'author': {
                'url': urljoin(response.url, author_name_tag.parent.attrs['href']),
                'name': author_name_tag.text
            },
            'tags_data': [
                {"name": tag.text, "url": urljoin(response.url, tag.attrs.get("href"))}
                for tag in soup.find_all("a", attrs={"class": "small"})
            ],
            'comments_data': self._get_comments(soup.find("comments").attrs.get("commentable-id")),
        }
        self._save(data)

    def _get_comments(self, post_id):
        api_path = f"/api/v2/comments?commentable_type=Post&commentable_id={post_id}&order=desc"
        response = self._get_response(urljoin(self.start_url, api_path))
        data = response.json()
        return data

    def _save(self, data: dict):
        self.db.add_post(data)


if __name__ == '__main__':
    client_db = pymongo.MongoClient()
    orm_database = Database('sqlite:///gb_blog_parse.db')
    parser = GbBlogParse('https://gb.ru/posts', orm_database)
    parser.run()
