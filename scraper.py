import urllib.parse
import re
import requests
from bs4 import BeautifulSoup

AMAZON_ASSOCIATE_TAG = "pricedekho085-21"
FLIPKART_AFF_ID = "youraffid"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

def clean_price(price_str):
    if not price_str:
        return 0
    numeric_value = re.sub(r'[^\d]', '', str(price_str))
    return int(numeric_value) if numeric_value else 0

def get_amazon_live_results(query):
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.amazon.in/s?k={encoded_query}&tag={AMAZON_ASSOCIATE_TAG}"
    items = []
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=5)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "html.parser")
            # Amazon search result cards
            cards = soup.select("div[data-component-type='s-search-result']")
            for card in cards[:4]:  # Top 4 products
                title_elem = card.select_one("h2 span")
                price_elem = card.select_one("span.a-price-whole")
                link_elem = card.select_one("h2 a")
                img_elem = card.select_one("img.s-image")

                if title_elem and price_elem:
                    title = title_elem.get_text(strip=True)
                    price = f"₹{price_elem.get_text(strip=True)}"
                    link = "https://www.amazon.in" + link_elem['href'] if link_elem else url
                    if AMAZON_ASSOCIATE_TAG not in link:
                        link += f"&tag={AMAZON_ASSOCIATE_TAG}"
                    img = img_elem['src'] if img_elem else ""

                    items.append({
                        "platform": "Amazon",
                        "title": title,
                        "price": price,
                        "numeric_price": clean_price(price),
                        "badge_color": "#ff9900",
                        "buy_url": link,
                        "image": img
                    })
    except Exception as e:
        print("Amazon live fetch error:", e)

    # Fallback agar block ho jaye
    if not items:
        items.append({
            "platform": "Amazon",
            "title": f"{query.title()} (Latest Variant)",
            "price": "Check Live Price",
            "numeric_price": 0,
            "badge_color": "#ff9900",
            "buy_url": url,
            "image": ""
        })
    return items

def get_flipkart_live_results(query):
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.flipkart.com/search?q={encoded_query}&affid={FLIPKART_AFF_ID}"
    items = []
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=5)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "html.parser")
            # Flipkart phones listing classes
            cards = soup.select("div._1AtVbE, div.tUxRFH, div._75nlfW")
            for card in cards[:4]:
                title_elem = card.select_one("div.KzDlHZ, div._4rR01T, a.wjcEIp")
                price_elem = card.select_one("div.Nx9bqj, div._30jeq3")
                link_elem = card.select_one("a.CGtC5Q, a._1fQZEK, a.VJA3rP")

                if title_elem and price_elem:
                    title = title_elem.get_text(strip=True)
                    price = price_elem.get_text(strip=True)
                    link = "https://www.flipkart.com" + link_elem['href'] if link_elem else url

                    items.append({
                        "platform": "Flipkart",
                        "title": title,
                        "price": price,
                        "numeric_price": clean_price(price),
                        "badge_color": "#2874f0",
                        "buy_url": link,
                        "image": ""
                    })
    except Exception as e:
        print("Flipkart live fetch error:", e)

    if not items:
        items.append({
            "platform": "Flipkart",
            "title": f"{query.title()} (Flipkart Assured)",
            "price": "Check Live Price",
            "numeric_price": 0,
            "badge_color": "#2874f0",
            "buy_url": url,
            "image": ""
        })
    return items

def fetch_all_deals(query):
    deals = []
    # Live Results dono platform se mangwayein
    deals.extend(get_amazon_live_results(query))
    deals.extend(get_flipkart_live_results(query))

    # Croma & Reliance ke quick direct comparisons
    encoded_query = urllib.parse.quote(query)
    deals.append({
        "platform": "Croma (Tata)",
        "title": f"{query.title()} on Croma",
        "price": "Check Store Offers",
        "numeric_price": 0,
        "badge_color": "#00b5b8",
        "buy_url": f"https://www.croma.com/searchB?q={encoded_query}",
        "image": ""
    })
    deals.append({
        "platform": "Reliance Digital",
        "title": f"{query.title()} on Reliance Digital",
        "price": "Check Instant Cashback",
        "numeric_price": 0,
        "badge_color": "#e42529",
        "buy_url": f"https://www.reliancedigital.in/search?q={encoded_query}",
        "image": ""
    })
    return deals
