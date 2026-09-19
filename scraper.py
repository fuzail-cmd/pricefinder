import urllib.parse
import re
import requests
from bs4 import BeautifulSoup

# Amazon direct Associate Tag
AMAZON_ASSOCIATE_TAG = "pricedekho085-21"

# EarnKaro Base Shortener Link
EARNKARO_FLIPKART_LINK = "https://fktr.in/BFCBBQ4"

AMAZON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-IN,en-GB;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Referer": "https://www.google.com/"
}

FLIPKART_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.google.com/"
}

COLORS_LIST = [
    "Titanium Black", "Titanium Gray", "Natural Titanium", "Desert Titanium",
    "Phantom Black", "Midnight", "Starlight", "Obsidian", "Bay Blue",
    "Black", "White", "Blue", "Green", "Gold", "Silver", "Grey", 
    "Purple", "Red", "Yellow", "Orange", "Pink", "Violet", "Cream"
]

def clean_price(price_str):
    if not price_str:
        return 0
    numeric_value = re.sub(r'[^\d]', '', str(price_str))
    return int(numeric_value) if numeric_value else 0

def extract_phone_specs(title, query=""):
    specs = {
        "model": "",
        "ram": "",
        "color": "",
        "storage": ""
    }
    
    clean_t = title.replace("(", " ").replace(")", " ").replace(",", " ")

    # 1. RAM Extraction
    ram_combo = re.search(r'(\d+)\s*GB\s*[\/\+]\s*(\d+)\s*(GB|TB)', clean_t, re.IGNORECASE)
    if ram_combo:
        specs["ram"] = f"{ram_combo.group(1)}GB"
        specs["storage"] = f"{ram_combo.group(2)}{ram_combo.group(3).upper()}"
    else:
        ram_match = re.search(r'\b(\d+)\s*GB\s*RAM\b', clean_t, re.IGNORECASE)
        if ram_match:
            specs["ram"] = f"{ram_match.group(1)}GB"

    # 2. Storage Extraction
    if not specs["storage"]:
        storage_match = re.search(r'\b(64|128|256|512)\s*GB\b|\b(1|2)\s*TB\b', clean_t, re.IGNORECASE)
        if storage_match:
            val = storage_match.group(0).upper().replace(" ", "")
            if specs.get("ram") != val:
                specs["storage"] = val

    # 3. Color Extraction
    for c in COLORS_LIST:
        if re.search(rf'\b{re.escape(c)}\b', title, re.IGNORECASE):
            specs["color"] = c
            break

    # 4. Smart Model Name
    model_match = re.search(r'((?:Samsung|Apple|iPhone|OnePlus|Realme|Redmi|Xiaomi|iQOO|Vivo|Oppo|Motorola|Poco|Google Pixel)\s+[A-Za-z0-9\+\s]+?)(?=\s*\(|\s*\d+\s*GB|\s*5G|\s*,|$)', title, re.IGNORECASE)
    if model_match:
        specs["model"] = model_match.group(1).strip()
    else:
        specs["model"] = query.title()

    # Smart fallbacks
    is_iphone = "iphone" in (query.lower() + title.lower())
    if not specs["storage"]:
        specs["storage"] = "128GB" if is_iphone else "256GB"
    if not specs["ram"]:
        specs["ram"] = "8GB" if is_iphone else "12GB"
    if not specs["color"]:
        specs["color"] = "Standard Edition"

    return specs

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
            
            for card in cards[:6]:
                title_elem = card.select_one("h2 span")
                price_whole = card.select_one("span.a-price-whole")
                link_elem = card.select_one("h2 a")
                img_elem = card.select_one("img.s-image")

                if title_elem:
                    full_title = title_elem.get_text(strip=True)
                    price = "Check Live Deal"
                    num_p = 0
                    if price_whole:
                        price_val = price_whole.get_text(strip=True).replace('.', '').strip()
                        price = f"₹{price_val}"
                        num_p = clean_price(price_val)
                    
                    link = "https://www.amazon.in" + link_elem['href'] if link_elem else url
                    if AMAZON_ASSOCIATE_TAG not in link:
                        link += f"&tag={AMAZON_ASSOCIATE_TAG}"
                        
                    img = img_elem['src'] if img_elem else ""
                    specs = extract_phone_specs(full_title, query)

                    items.append({
                        "platform": "Amazon",
                        "title": full_title[:75] + ("..." if len(full_title) > 75 else ""),
                        "price": price,
                        "numeric_price": num_p,
                        "badge_color": "#ff9900",
                        "buy_url": link,
                        "image": img,
                        "specs": specs
                    })
    except Exception as err:
        print(f"Amazon error: {err}")

    return items

def get_flipkart_live_results(query):
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://www.flipkart.com/search?q={encoded_query}"
    items = []
    
    try:
        session = requests.Session()
        resp = session.get(search_url, headers=FLIPKART_HEADERS, timeout=8)
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "html.parser")
            cards = soup.select("div[data-id], div._1AtVbE, div.tUxRFH, div._75nlfW")
            
            for card in cards:
                if len(items) >= 5:
                    break
                    
                title_elem = card.select_one("div.KzDlHZ, div._4rR01T, a.wjcEIp, div._2WkVRV")
                price_elem = card.select_one("div.Nx9bqj, div._30jeq3, div._25b18c")
                link_elem = card.select_one("a[href*='/p/'], a.CGtC5Q, a._1fQZEK")
                img_elem = card.select_one("img.DByuf4, img._396cs4, img")
                
                if title_elem:
                    full_title = title_elem.get_text(strip=True)
                    price = price_elem.get_text(strip=True) if price_elem else "Check Live Deal"
                    num_p = clean_price(price) if price_elem else 0
                    img = img_elem['src'] if img_elem else ""
                    
                    specs = extract_phone_specs(full_title, query)

                    # EarnKaro link lagaya gaya hai
                    items.append({
                        "platform": "Flipkart",
                        "title": full_title[:75] + ("..." if len(full_title) > 75 else ""),
                        "price": price,
                        "numeric_price": num_p,
                        "badge_color": "#2874f0",
                        "buy_url": EARNKARO_FLIPKART_LINK,
                        "image": img,
                        "specs": specs
                    })
    except Exception as err:
        print(f"Flipkart error: {err}")

    if not items:
        specs = extract_phone_specs(query, query)
        items.append({
            "platform": "Flipkart",
            "title": f"{query.title()} on Flipkart",
            "price": "Check Live Deal",
            "numeric_price": 0,
            "badge_color": "#2874f0",
            "buy_url": EARNKARO_FLIPKART_LINK,
            "image": "",
            "specs": specs
        })

    return items

def fetch_all_deals(query):
    live_deals = []
    
    # 1. Amazon live results (Direct Associates tag)
    live_deals.extend(get_amazon_live_results(query))
    
    # 2. Flipkart live results (EarnKaro monetization)
    live_deals.extend(get_flipkart_live_results(query))

    # 3. High-to-low price sorting
    priced_items = [d for d in live_deals if d.get("numeric_price", 0) > 0]
    priced_items.sort(key=lambda x: x["numeric_price"], reverse=True)

    unpriced_items = [d for d in live_deals if d.get("numeric_price", 0) == 0]

    # 4. Secondary Stores
    encoded_query = urllib.parse.quote(query)
    base_specs = extract_phone_specs(query, query)
    other_stores = [
        {
            "platform": "Croma (Tata)",
            "title": f"{query.title()} on Croma Store",
            "price": "Check Store Offers",
            "numeric_price": 0,
            "badge_color": "#00b5b8",
            "buy_url": f"https://www.croma.com/searchB?q={encoded_query}",
            "image": "",
            "specs": base_specs
        },
        {
            "platform": "Reliance Digital",
            "title": f"{query.title()} on Reliance Digital",
            "price": "Check Instant Cashback",
            "numeric_price": 0,
            "badge_color": "#e42529",
            "buy_url": f"https://www.reliancedigital.in/search?q={encoded_query}",
            "image": "",
            "specs": base_specs
        },
        {
            "platform": "Tata CLiQ",
            "title": f"{query.title()} on Tata CLiQ",
            "price": "Check Brand Warranty",
            "numeric_price": 0,
            "badge_color": "#212121",
            "buy_url": f"https://www.tatacliq.com/search/?searchCategory=all&text={encoded_query}",
            "image": "",
            "specs": base_specs
        }
    ]

    return priced_items + unpriced_items + other_stores
