from setuptools import setup, find_packages


setup(
    name = 'mechanical_scraper',
    version = '2.0',
    description = 'Reduce your development time using this library based on requests and bs4.BeautifulSoup.',
    url = 'https://github.com/wsder31/mechanical_scraper.git',
    author = '실사코',
    author_email = 'silsako@naver.com',
    license = 'Apache-2.0 license',
    packages = find_packages(),
    install_requires = ['autopep8', 'bs4', 'lxml', 'requests', 'requests-html'],
)
