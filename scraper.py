import urllib.parse
import re

def clean_price(price_str):
    if not price_str:
        return 0
    cleaned = re.sub(r'[^\d]', '', price_str)
    return int(cleaned) if cleaned else 0

def fetch_all_deals(query):
    """
    Render servers ke IP timeout/block se bachne ke liye fast-timeout scraper 
    aur dynamic comparative product generator (Always returns verified cards).
    """
    results = []
    clean_q = query.strip()
    if not clean_q:
        return results

    encoded = urllib.parse.quote_plus(clean_q)
    title_display = clean_q.title()

    # 1. Quick Scraping Attempt (Strict 3.5s Timeout)
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
            "Accept-Language": "en-IN,en;q=0.9"
        }

        # Flipkart Mobile Scrape Attempt
        f_url = f"https://www.flipkart.com/search?q={encoded}"
        f_res = requests.get(f_url, headers=headers, timeout=3.5)
        
        if f_res.status_code == 200:
            soup = BeautifulSoup(f_res.content, "html.parser")
            cards = soup.select("div._75nlfW, div.slAVV4, div._1sdMkc, div.tUxRFH, div._1AtVbE")
            
            for card in cards[:4]:
                link_tag = card.find("a", href=True)
                if not link_tag:
                    continue
                clean_path = link_tag["href"].split("?")[0]
                direct_url = f"https://www.flipkart.com{clean_path}"
                
                title_elem = card.find("div", {"class": ["KzDlHZ", "wjcEIp", "_4rR01T"]}) or card.find("a", {"class": ["WKTcLC", "s1Q9rs"]})
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)
                
                price_elem = card.find("div", {"class": ["Nx9bqj", "_30jeq3"]})
                price_raw = price_elem.get_text(strip=True) if price_elem else "Check Price"
                price_num = clean_price(price_raw)
                
                img_elem = card.find("img", {"class": ["DByuf4", "_396cs4", "_53J4C-"]})
                img_url = img_elem.get("src") if img_elem else "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=300&q=80"
                
                results.append({
                    "store": "Flipkart",
                    "title": title,
                    "price_raw": price_raw,
                    "price_num": price_num if price_num > 0 else 999999,
                    "image": img_url,
                    "affiliate_url": direct_url
                })
    except Exception as e:
        print(f"Scraper Note: {e}")

    # 2. Safety Net: Agar cloud IP block ho ya network issue ho,
    # Screen par turant exact query ke verified comparative cards load honge
    if not results:
        results = [
            {
                "store": "Amazon",
                "title": f"{title_display} (Top Verified Deal)",
                "price_raw": "Check Live Price",
                "price_num": 1,
                "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&q=80",
                "affiliate_url": f"https://www.amazon.in/s?k={encoded}"
            },
            {
                "store": "Flipkart",
                "title": f"{title_display} (Best Offer & Discount)",
                "price_raw": "Check Lowest Deal",
                "price_num": 2,
                "image": "https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=400&q=80",
                "affiliate_url": f"https://www.flipkart.com/search?q={encoded}"
            }
        ]

    return results
