import urllib.parse
import re
import requests
from bs4 import BeautifulSoup

AMAZON_ASSOCIATE_TAG = "pricedekho085-21"
FLIPKART_AFF_ID = "youraffid"

# Desktop Headers for Amazon
AMAZON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-IN,en-GB;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Referer": "https://www.google.com/"
}

# Mobile/API-friendly Headers for Flipkart to bypass desktop block
FLIPKART_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.google.com/"
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
        session = requests.Session()
        resp = session.get(url, headers=AMAZON_HEADERS, timeout=8)
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "html.parser")
            cards = soup.select("div[data-component-type='s-search-result']")
            
            # Top 8 products fetch karega
            for card in cards[:8]:
                title_elem = card.select_one("h2 span")
                price_whole = card.select_one("span.a-price-whole")
                link_elem = card.select_one("h2 a")
                img_elem = card.select_one("img.s-image")

                if title_elem and price_whole:
                    title = title_elem.get_text(strip=True)
                    price_val = price_whole.get_text(strip=True).replace('.', '').strip()
                    price = f"₹{price_val}"
                    
                    link = "https://www.amazon.in" + link_elem['href'] if link_elem else url
                    if AMAZON_ASSOCIATE_TAG not in link:
                        link += f"&tag={AMAZON_ASSOCIATE_TAG}"
                        
                    img = img_elem['src'] if img_elem else ""

                    items.append({
                        "platform": "Amazon",
                        "title": title[:70] + ("..." if len(title) > 70 else ""),
                        "price": price,
                        "numeric_price": clean_price(price),
                        "badge_color": "#ff9900",
                        "buy_url": link,
                        "image": img
                    })
    except Exception as err:
        print(f"Amazon error: {err}")

    if not items:
        items.append({
            "platform": "Amazon",
            "title": f"{query.title()} (Latest Online Price)",
            "price": "Check Live Deal",
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
        session = requests.Session()
        resp = session.get(url, headers=FLIPKART_HEADERS, timeout=8)
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "html.parser")
            
            # Flipkart product card containers (covers mobile & desktop layout)
            cards = soup.select("div[data-id], div._1AtVbE, div.tUxRFH, div._75nlfW")
            
            for card in cards:
                if len(items) >= 6:  # Top 6 Flipkart products
                    break
                    
                title_elem = card.select_one("div.KzDlHZ, div._4rR01T, a.wjcEIp, div._2WkVRV, div.row")
                price_elem = card.select_one("div.Nx9bqj, div._30jeq3, div._25b18c")
                link_elem = card.select_one("a[href*='/p/'], a.CGtC5Q, a._1fQZEK")
                img_elem = card.select_one("img.DByuf4, img._396cs4, img")

                if title_elem and price_elem:
                    title = title_elem.get_text(strip=True)
                    price = price_elem.get_text(strip=True)
                    href = link_elem['href'] if link_elem else ""
                    link = f"https://www.flipkart.com{href}" if href.startswith('/') else url
                    img = img_elem['src'] if img_elem else ""

                    items.append({
                        "platform": "Flipkart",
                        "title": title[:70] + ("..." if len(title) > 70 else ""),
                        "price": price,
                        "numeric_price": clean_price(price),
                        "badge_color": "#2874f0",
                        "buy_url": link,
                        "image": img
                    })
    except Exception as err:
        print(f"Flipkart error: {err}")

    if not items:
        items.append({
            "platform": "Flipkart",
            "title": f"{query.title()} on Flipkart",
            "price": "Check Live Deal",
            "numeric_price": 0,
            "badge_color": "#2874f0",
            "buy_url": url,
            "image": ""
        })
    return items

def fetch_all_deals(query):
    deals = []
    
    # Live Results fetch
    deals.extend(get_amazon_live_results(query))
    deals.extend(get_flipkart_live_results(query))

    # Croma & Reliance quick search links
    encoded_query = urllib.parse.quote(query)
    deals.append({
        "platform": "Croma (Tata)",
        "title": f"{query.title()} on Croma",
        "price": "Check Offers",
        "numeric_price": 0,
        "badge_color": "#00b5b8",
        "buy_url": f"https://www.croma.com/searchB?q={encoded_query}",
        "image": ""
    })
    deals.append({
        "platform": "Reliance Digital",
        "title": f"{query.title()} on Reliance Digital",
        "price": "Check Offers",
        "numeric_price": 0,
        "badge_color": "#e42529",
        "buy_url": f"https://www.reliancedigital.in/search?q={encoded_query}",
        "image": ""
    })
    return deals
