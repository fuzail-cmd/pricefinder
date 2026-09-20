import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

# Browser headers ko authentic banana
AMAZON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-IN,en-GB;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Device-Memory": "8",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1"
}

FLIPKART_HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9"
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
        session = requests.Session()
        response = session.get(url, headers=AMAZON_HEADERS, timeout=6)
        
        # Check agar captcha ya bot block aaya
        if "api-services-support@amazon.com" in response.text or "Type the characters you see in this image" in response.text:
            print("Amazon CAPTCHA block encountered.")
            return deals

        soup = BeautifulSoup(response.content, "html.parser")
        items = soup.find_all("div", {"data-component-type": "s-search-result"})
        
        for item in items[:5]:
            title_elem = item.find("h2")
            if not title_elem:
                continue
            
            link_tag = title_elem.find("a")
            if not link_tag or not link_tag.get("href"):
                continue
                
            title = title_elem.get_text(strip=True)
            raw_href = link_tag["href"]
            
            # Canonical product direct link
            if "/dp/" in raw_href:
                asin = raw_href.split("/dp/")[1].split("/")[0].split("?")[0]
                direct_url = f"https://www.amazon.in/dp/{asin}"
            else:
                direct_url = "https://www.amazon.in" + raw_href.split("?")[0]

            price_elem = item.find("span", {"class": "a-price-whole"})
            price_raw = price_elem.get_text(strip=True) if price_elem else ""
            price_num = clean_price(price_raw)
            
            img_elem = item.find("img", {"class": "s-image"})
            img_url = img_elem["src"] if img_elem else "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=300&q=80"
            
            if price_num > 0:
                deals.append({
                    "store": "Amazon",
                    "title": title,
                    "price_raw": f"₹{price_num:,}",
                    "price_num": price_num,
                    "image": img_url,
                    "affiliate_url": direct_url
                })
    except Exception as e:
        print(f"Amazon Error: {e}")
        
    return deals

def scrape_flipkart(query):
    deals = []
    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://www.flipkart.com/search?q={encoded_query}"
    
    try:
        session = requests.Session()
        response = session.get(url, headers=FLIPKART_HEADERS, timeout=6)
        
        if response.status_code != 200:
            return deals
            
        soup = BeautifulSoup(response.content, "html.parser")
        
        cards = soup.select("div._75nlfW, div.slAVV4, div._1sdMkc, div.tUxRFH, div._1AtVbE")
        for card in cards[:5]:
            link_tag = card.find("a", href=True)
            if not link_tag:
                continue
                
            raw_href = link_tag["href"]
            clean_path = raw_href.split("?")[0]
            direct_url = f"https://www.flipkart.com{clean_path}"
            
            title_elem = card.find("div", {"class": ["KzDlHZ", "wjcEIp", "_4rR01T"]}) or card.find("a", {"class": ["WKTcLC", "s1Q9rs"]})
            if not title_elem:
                continue
            title = title_elem.get_text(strip=True)
            
            price_elem = card.find("div", {"class": ["Nx9bqj", "_30jeq3"]})
            price_raw = price_elem.get_text(strip=True) if price_elem else ""
            price_num = clean_price(price_raw)
            
            img_elem = card.find("img", {"class": ["DByuf4", "_396cs4", "_53J4C-"]})
            img_url = img_elem.get("src") if img_elem else "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=300&q=80"
            
            if price_num > 0:
                deals.append({
                    "store": "Flipkart",
                    "title": title,
                    "price_raw": f"₹{price_num:,}",
                    "price_num": price_num,
                    "image": img_url,
                    "affiliate_url": direct_url
                })
    except Exception as e:
        print(f"Flipkart Error: {e}")
        
    return deals

def fetch_all_deals(query):
    results = []
    if not query:
        return results

    # Scrape live deals
    amazon_data = scrape_amazon(query)
    flipkart_data = scrape_flipkart(query)
    
    results.extend(amazon_data)
    results.extend(flipkart_data)
    
    # AGAR RENDER KO IP BLOCK KI WAJAH SE 0 RESULTS MILE (Safety Fallback):
    # Website blank nahi hogi, clean comparative cards auto-generate ho jayenge
    if not results:
        encoded = urllib.parse.quote_plus(query)
        clean_title = query.title()
        
        fallback_deals = [
            {
                "store": "Amazon",
                "title": f"{clean_title} (Best Deal on Amazon)",
                "price_raw": "Check Best Live Price",
                "price_num": 1,
                "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&q=80",
                "affiliate_url": f"https://www.amazon.in/s?k={encoded}"
            },
            {
                "store": "Flipkart",
                "title": f"{clean_title} (Lowest Price on Flipkart)",
                "price_raw": "Check Lowest Deal",
                "price_num": 2,
                "image": "https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=400&q=80",
                "affiliate_url": f"https://www.flipkart.com/search?q={encoded}"
            }
        ]
        return fallback_deals
        
    results.sort(key=lambda x: x["price_num"])
    return results
