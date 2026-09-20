import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

def clean_price(price_str):
    if not price_str:
        return 0
    cleaned = re.sub(r'[^\d]', '', price_str)
    return int(cleaned) if cleaned else 0

def scrape_amazon(query):
    deals = []
    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://www.amazon.in/s?k={encoded_query}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        items = soup.find_all("div", {"data-component-type": "s-search-result"})
        
        for item in items[:6]:
            # Title & Direct Link
            title_elem = item.find("h2")
            if not title_elem:
                continue
            
            link_tag = title_elem.find("a")
            if not link_tag or not link_tag.get("href"):
                continue
            
            title = title_elem.get_text(strip=True)
            raw_href = link_tag["href"]
            
            # ASIN nikaal kar exact direct canonical product URL banana
            if "/dp/" in raw_href:
                asin = raw_href.split("/dp/")[1].split("/")[0].split("?")[0]
                direct_url = f"https://www.amazon.in/dp/{asin}"
            else:
                clean_path = raw_href.split("?")[0]
                direct_url = f"https://www.amazon.in{clean_path}"
                
            # Price
            price_elem = item.find("span", {"class": "a-price-whole"})
            price_raw = price_elem.get_text(strip=True) if price_elem else ""
            price_num = clean_price(price_raw)
            
            # Image
            img_elem = item.find("img", {"class": "s-image"})
            img_url = img_elem["src"] if img_elem else ""
            
            if price_num > 0 and img_url:
                deals.append({
                    "store": "Amazon",
                    "title": title,
                    "price_raw": f"₹{price_num:,}",
                    "price_num": price_num,
                    "image": img_url,
                    "affiliate_url": direct_url
                })
    except Exception as e:
        print(f"Amazon Scrape Error: {e}")
        
    return deals

def scrape_flipkart(query):
    deals = []
    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://www.flipkart.com/search?q={encoded_query}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Flipkart cards selector
        cards = soup.select("div._75nlfW, div.slAVV4, div._1sdMkc, div.tUxRFH, div._1AtVbE")
        if not cards:
            cards = soup.find_all("div", {"data-id": True})
            
        for card in cards[:6]:
            link_tag = card.find("a", href=True)
            if not link_tag:
                continue
                
            raw_href = link_tag["href"]
            # Direct product link (/p/ URL)
            clean_path = raw_href.split("?")[0]
            direct_url = f"https://www.flipkart.com{clean_path}"
            
            # Title
            title_elem = card.find("div", {"class": ["KzDlHZ", "wjcEIp", "_4rR01T"]}) or card.find("a", {"class": ["WKTcLC", "s1Q9rs"]})
            if not title_elem:
                continue
            title = title_elem.get_text(strip=True)
            
            # Price
            price_elem = card.find("div", {"class": ["Nx9bqj", "_30jeq3"]})
            price_raw = price_elem.get_text(strip=True) if price_elem else ""
            price_num = clean_price(price_raw)
            
            # Image
            img_elem = card.find("img", {"class": ["DByuf4", "_396cs4", "_53J4C-"]})
            img_url = img_elem.get("src") if img_elem else ""
            
            if price_num > 0 and img_url:
                deals.append({
                    "store": "Flipkart",
                    "title": title,
                    "price_raw": f"₹{price_num:,}",
                    "price_num": price_num,
                    "image": img_url,
                    "affiliate_url": direct_url
                })
    except Exception as e:
        print(f"Flipkart Scrape Error: {e}")
        
    return deals

def fetch_all_deals(query):
    # Local list - taaki purana search memory me na atke
    results = []
    if not query:
        return results
        
    amazon_data = scrape_amazon(query)
    flipkart_data = scrape_flipkart(query)
    
    results.extend(amazon_data)
    results.extend(flipkart_data)
    
    # Lowest price pehle
    results.sort(key=lambda x: x["price_num"])
    return results
