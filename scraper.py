import urllib.parse
import re

def clean_price(price_str):
    if not price_str:
        return 0
    cleaned = re.sub(r'[^\d]', '', price_str)
    return int(cleaned) if cleaned else 0

def fetch_all_deals(query):
    results = []
    clean_q = query.strip()
    if not clean_q:
        return results

    encoded = urllib.parse.quote_plus(clean_q)
    title_text = clean_q.title()

    # Pehle live Flipkart scrape karne ka try karega
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
            "Accept-Language": "en-IN,en;q=0.9"
        }

        f_url = f"https://www.flipkart.com/search?q={encoded}"
        res = requests.get(f_url, headers=headers, timeout=3)

        if res.status_code == 200:
            soup = BeautifulSoup(res.content, "html.parser")
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
                    "price_num": price_num if price_num > 0 else 99999,
                    "image": img_url,
                    "affiliate_url": direct_url
                })
    except Exception as e:
        pass

    # AGAR RENDER KE IP PAR SCRAPING BLOCK HO:
    # Screen bilkul khali nahi rahegi! Direct model landing link aur visual card guaranteed aayega.
    if not results:
        results = [
            {
                "store": "Amazon",
                "title": f"{title_text} (Check Direct Model Deal)",
                "price_raw": "Live Price Check",
                "price_num": 1,
                "image": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=300&q=80",
                "affiliate_url": f"https://www.amazon.in/s?k={encoded}"
            },
            {
                "store": "Flipkart",
                "title": f"{title_text} (Best Online Discount)",
                "price_raw": "Live Offer Check",
                "price_num": 2,
                "image": "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=300&q=80",
                "affiliate_url": f"https://www.flipkart.com/search?q={encoded}"
            }
        ]

    return results
