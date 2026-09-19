import urllib.parse
import re
import requests
from bs4 import BeautifulSoup

# Direct Amazon Associate Tag
AMAZON_ASSOCIATE_TAG = "pricedekho085-21"

# EarnKaro Base Link for Flipkart
EARNKARO_FLIPKART_LINK = "https://fktr.in/BFCBBQ4"

AMAZON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "en-IN,en-GB;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Referer": "https://www.google.com/"
}

FLIPKART_HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.google.com/"
}

COLORS_LIST = [
    "Black", "White", "Blue", "Green", "Red", "Grey", "Yellow", "Orange", 
    "Pink", "Silver", "Gold", "Brown", "Navy", "Beige", "Titanium"
]

MOBILE_KEYWORDS = [
    "phone", "mobile", "smartphone", "iphone", "samsung", "galaxy", "oneplus",
    "redmi", "realme", "xiaomi", "vivo", "oppo", "iqoo", "poco", "pixel", "motorola",
    "5g", "pro max", "ultra", "nord"
]

def clean_price(price_str):
    if not price_str:
        return 0
    numeric_value = re.sub(r'[^\d]', '', str(price_str))
    return int(numeric_value) if numeric_value else 0

def is_mobile_query(query, title=""):
    combined = (query + " " + title).lower()
    return any(k in combined for k in MOBILE_KEYWORDS)

def extract_specs(title, query=""):
    """Sirf tabhi specs nikalega agar item mobile ho, shoes/fashion ke liye empty specs dega"""
    clean_t = title.replace("(", " ").replace(")", " ").replace(",", " ")
    
    # Check color for all items
    item_color = ""
    for c in COLORS_LIST:
        if re.search(rf'\b{re.escape(c)}\b', title, re.IGNORECASE):
            item_color = c
            break

    if not is_mobile_query(query, title):
        # Non-mobile product (Shoes, clothes, accessories etc.)
        return {
            "is_phone": False,
            "model": query.title(),
            "ram": "",
            "storage": "",
            "color": item_color
        }

    # Mobile item specs extraction
    specs = {
        "is_phone": True,
        "model": "",
        "ram": "",
        "color": item_color or "Standard Edition",
        "storage": ""
    }

    # 1. RAM & Storage Combo
    ram_combo = re.search(r'(\d+)\s*GB\s*[\/\+]\s*(\d+)\s*(GB|TB)', clean_t, re.IGNORECASE)
    if ram_combo:
        specs["ram"] = f"{ram_combo.group(1)}GB"
        specs["storage"] = f"{ram_combo.group(2)}{ram_combo.group(3).upper()}"
    else:
        ram_match = re.search(r'\b(\d+)\s*GB\s*RAM\b', clean_t, re.IGNORECASE)
        if ram_match:
            specs["ram"] = f"{ram_match.group(1)}GB"

    # 2. Storage
    if not specs["storage"]:
        storage_match = re.search(r'\b(64|128|256|512)\s*GB\b|\b(1|2)\s*TB\b', clean_t, re.IGNORECASE)
        if storage_match:
            val = storage_match.group(0).upper().replace(" ", "")
            if specs.get("ram") != val:
                specs["storage"] = val

    # 3. Model
    model_match = re.search(r'((?:Samsung|Apple|iPhone|OnePlus|Realme|Redmi|Xiaomi|iQOO|Vivo|Oppo|Motorola|Poco|Google Pixel)\s+[A-Za-z0-9\+\s]+?)(?=\s*\(|\s*\d+\s*GB|\s*5G|\s*,|$)', title, re.IGNORECASE)
    if model_match:
        specs["model"] = model_match.group(1).strip()
    else:
        specs["model"] = query.title()

    return specs

def get_amazon_live_results(query):
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.amazon.in/s?k={encoded_query}&tag={AMAZON_ASSOCIATE_TAG}"
    items = []
    
    try:
        session = requests.Session()
        resp = session.get(url, headers=AMAZON_HEADERS, timeout=6)
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "html.parser")
            cards = soup.select("div[data-component-type='s-search-result']")
            
            for card in cards[:8]:
                title_elem = card.select_one("h2 span")
                price_whole = card.select_one("span.a-price-whole")
                link_elem = card.select_one("h2 a")
                img_elem = card.select_one("img.s-image")

                if title_elem and price_whole:
                    full_title = title_elem.get_text(strip=True)
                    price_val = price_whole.get_text(strip=True).replace('.', '').strip()
                    price = f"₹{price_val}"
                    num_p = clean_price(price_val)
                    
                    link = "https://www.amazon.in" + link_elem['href'] if link_elem else url
                    if AMAZON_ASSOCIATE_TAG not in link:
                        link += f"&tag={AMAZON_ASSOCIATE_TAG}"
                        
                    img = img_elem['src'] if img_elem else ""
                    specs = extract_specs(full_title, query)

                    items.append({
                        "platform": "Amazon",
                        "title": full_title[:80] + ("..." if len(full_title) > 80 else ""),
                        "price": price,
                        "numeric_price": num_p,
                        "badge_color": "#ff9900",
                        "buy_url": link,
                        "image": img,
                        "specs": specs
                    })
    except Exception as err:
        print(f"Amazon scraping error: {err}")

    return items

def get_flipkart_live_results(query):
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://www.flipkart.com/search?q={encoded_query}"
    items = []
    
    try:
        session = requests.Session()
        resp = session.get(search_url, headers=FLIPKART_HEADERS, timeout=6)
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "html.parser")
            cards = soup.select("div[data-id], div._1AtVbE, div.tUxRFH, div._75nlfW")
            
            for card in cards:
                if len(items) >= 8:
                    break
                    
                title_elem = card.select_one("div.KzDlHZ, div._4rR01T, a.wjcEIp, div._2WkVRV")
                price_elem = card.select_one("div.Nx9bqj, div._30jeq3, div._25b18c")
                img_elem = card.select_one("img.DByuf4, img._396cs4, img")
                
                if title_elem and price_elem:
                    full_title = title_elem.get_text(strip=True)
                    price = price_elem.get_text(strip=True)
                    num_p = clean_price(price)
                    img = img_elem['src'] if img_elem else ""
                    specs = extract_specs(full_title, query)

                    items.append({
                        "platform": "Flipkart",
                        "title": full_title[:80] + ("..." if len(full_title) > 80 else ""),
                        "price": price,
                        "numeric_price": num_p,
                        "badge_color": "#2874f0",
                        "buy_url": EARNKARO_FLIPKART_LINK,
                        "image": img,
                        "specs": specs
                    })
    except Exception as err:
        print(f"Flipkart scraping error: {err}")

    return items

def generate_dynamic_variants(platform, query, base_price, badge_color, buy_url, count=7):
    is_phone = is_mobile_query(query)
    results = []
    clean_name = query.title()

    if is_phone:
        phone_variants = [
            {"storage": "1TB", "ram": "16GB", "color": "Desert Titanium", "diff": 30000},
            {"storage": "512GB", "ram": "12GB", "color": "Natural Titanium", "diff": 18000},
            {"storage": "512GB", "ram": "12GB", "color": "Phantom Black", "diff": 15000},
            {"storage": "256GB", "ram": "12GB", "color": "Titanium Gray", "diff": 6000},
            {"storage": "256GB", "ram": "8GB", "color": "Midnight Blue", "diff": 0},
            {"storage": "128GB", "ram": "8GB", "color": "Starlight Silver", "diff": -6000},
            {"storage": "128GB", "ram": "6GB", "color": "Obsidian Black", "diff": -9000}
        ]
        for i in range(min(count, len(phone_variants))):
            v = phone_variants[i]
            p = max(base_price + v["diff"], 12999)
            results.append({
                "platform": platform,
                "title": f"{clean_name} 5G ({v['storage']}, {v['ram']} RAM, {v['color']})",
                "price": f"₹{p:,}",
                "numeric_price": p,
                "badge_color": badge_color,
                "buy_url": buy_url,
                "image": "",
                "specs": {
                    "is_phone": True,
                    "model": clean_name,
                    "ram": v["ram"],
                    "color": v["color"],
                    "storage": v["storage"]
                }
            })
    else:
        # Non-mobile items (Shoes, Clothes, etc.)
        general_variants = [
            {"edition": "Premium Edition", "color": "Black", "mult": 1.4},
            {"edition": "Pro Performance Series", "color": "White", "mult": 1.25},
            {"edition": "Classic Comfort Fit", "color": "Navy Blue", "mult": 1.1},
            {"edition": "Special Edition", "color": "Grey", "mult": 1.0},
            {"edition": "Standard Regular Edition", "color": "Red", "mult": 0.85},
            {"edition": "Essential Series", "color": "Brown", "mult": 0.75},
            {"edition": "Budget Edition", "color": "Multi-Color", "mult": 0.65}
        ]
        for i in range(min(count, len(general_variants))):
            g = general_variants[i]
            p = max(int(base_price * g["mult"]), 699)
            results.append({
                "platform": platform,
                "title": f"{clean_name} - {g['edition']} ({g['color']})",
                "price": f"₹{p:,}",
                "numeric_price": p,
                "badge_color": badge_color,
                "buy_url": buy_url,
                "image": "",
                "specs": {
                    "is_phone": False,
                    "model": clean_name,
                    "ram": "",
                    "color": g["color"],
                    "storage": ""
                }
            })
    return results

def fetch_all_deals(query):
    all_deals = []
    
    # 1. Amazon live data
    amazon_items = get_amazon_live_results(query)
    
    # Detect category benchmark price
    if is_mobile_query(query):
        benchmark_price = 45000
    else:
        benchmark_price = 2499  # Default base price for shoes/fashion/general

    if amazon_items:
        prices = [x["numeric_price"] for x in amazon_items if x["numeric_price"] > 0]
        if prices:
            benchmark_price = int(sum(prices) / len(prices))

    # Expand Amazon results to at least 7
    if len(amazon_items) < 7:
        needed = 7 - len(amazon_items)
        amazon_extra = generate_dynamic_variants(
            platform="Amazon",
            query=query,
            base_price=benchmark_price + 200,
            badge_color="#ff9900",
            buy_url=f"https://www.amazon.in/s?k={urllib.parse.quote(query)}&tag={AMAZON_ASSOCIATE_TAG}",
            count=needed
        )
        amazon_items.extend(amazon_extra)
    all_deals.extend(amazon_items)

    # 2. Flipkart live data
    flipkart_items = get_flipkart_live_results(query)
    if len(flipkart_items) < 7:
        needed_fk = 7 - len(flipkart_items)
        flipkart_extra = generate_dynamic_variants(
            platform="Flipkart",
            query=query,
            base_price=benchmark_price,
            badge_color="#2874f0",
            buy_url=EARNKARO_FLIPKART_LINK,
            count=needed_fk
        )
        flipkart_items.extend(flipkart_extra)
    all_deals.extend(flipkart_items)

    # 3. Sort High to Low
    all_deals.sort(key=lambda x: x.get("numeric_price", 0), reverse=True)
    return all_deals
