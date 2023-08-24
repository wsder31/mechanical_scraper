# Mechanical Scraper
> Mechanical Scraper - Web Scraping Easily  
> Make simple repetitive tasks convenient when developing a web scraping program.  
> Reduce your development time using this library based on requests and bs4.BeautifulSoup.

## Generating Code for HTTP Request
> Just copy and paste the http message obtained through tools such as Fiddler to automatically generate a request code.  
> Depending on the Content-Type, the appropriate code is automatically applied.  
> Update the session automatically.

![image](https://user-images.githubusercontent.com/63570918/229982297-97abb684-30d2-4a05-98bf-a09ce3d28cfd.png)
![image](https://user-images.githubusercontent.com/63570918/229980797-7949bdca-49d0-4ce8-a749-15cb1ae225a9.png)

## Selector Assistant
> A browser will automatically pop up about the http response. Then, you can easily copy css selectors via developer's tool.  
> Find out hidden data automatically.

![image](https://user-images.githubusercontent.com/63570918/233291454-72383ace-f6dc-4edc-abf9-9311b0926d82.png)

```python
from mechanical_scraper import MechanicalScraper


ms = MechanicalScraper()
ms.set_base_url('https://finance.naver.com/')

url = f'{ms.base_url}'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.54'
}

# If a value of True is entered in the second argument, a browser will automatically pop up about the http response. Then, you can easily copy css selectors via developer's tool.
response = ms.get(url, True, headers=headers)

response.raise_for_status()

bs = BeautifulSoup(response.text, 'html.parser')
elements = bs.select('#container > div.aside > div > div.aside_area.aside_popular > table > tbody > tr')
for el in elements:
    title = el.select_one('th > a').text.strip()
    price = el.select_one('td:nth-child(2)').text.replace(',', '').strip()
    link = ms.get_full_url(el.select_one('th > a')['href'])

    print(title, price, link)
    print()
```

## Video Guide
> https://youtu.be/ft2bzuLVfPs

## Donation
> [KakaoPay](https://qr.kakaopay.com/Ej9TdXTld138801559)

## Contact
> silsako@naver.com
