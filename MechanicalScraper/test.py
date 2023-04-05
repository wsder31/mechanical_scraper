from mechanical_scraper import MechanicalScraper
from bs4 import BeautifulSoup   # pip install bs4 lxml


ms = MechanicalScraper()

#region login page - get csrf_token
response = ms.get(
    "http://quotes.toscrape.com/login",
    # True,
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
        "Referer": "http://quotes.toscrape.com/",
    },
)

response.raise_for_status()

bs = BeautifulSoup(response.text, 'lxml')

csrf_token = bs.select_one('body > div > form > input[type=hidden]:nth-child(1)')['value']
#endregion

#region login
response = ms.post(
    "http://quotes.toscrape.com/login",
    data={
        "csrf_token": [csrf_token],
        "username": ["test"],
        "password": ["test"],
    },
    headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
        "Referer": "http://quotes.toscrape.com/login",
    },
)

response.raise_for_status()
#endregion

#region scrap books
response = ms.get(
    "http://quotes.toscrape.com/",
    True,
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
        "Referer": "http://quotes.toscrape.com/login",
    },
)

response.raise_for_status()

bs = BeautifulSoup(response.text, 'lxml')

elements = bs.select('body > div > div:nth-child(2) > div.col-md-8 > div')
for el in elements:
    title = el.select_one('span.text').text
    author = el.select_one('span:nth-child(2) > small').text
    print(f"title: {title}")
    print(f"author: {author}")
    print()
#endregion

print()
