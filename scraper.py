import urllib.parse
import re

# Affiliate IDs / Aggregator Tags
AMAZON_TAG = "yourtag-21"
FLIPKART_AFF_ID = "youraffid"
EARNKARO_REF = "your_earnkaro_id"

def clean_price(price_str):
    if not price_str:
        return 0
    numeric_value = re.sub(r'[^\d]', '', str(price_str))
    return int(numeric_value) if numeric_value else 0

def fetch_all_deals(query):
    encoded_query = urllib.parse.quote(query)
    
    # India ke sabhi top genuine platforms ki dynamic mapping
    deals = [
        {
            "platform": "Amazon",
            "title": f"{query.title()} on Amazon India",
            "price": "Check Best Deal",
            "numeric_price": 100,
            "badge_color": "#ff9900",
            "buy_url": f"https://www.amazon.in/s?k={encoded_query}&tag={AMAZON_TAG}"
        },
        {
            "platform": "Flipkart",
            "title": f"{query.title()} on Flipkart",
            "price": "Check Best Deal",
            "numeric_price": 101,
            "badge_color": "#2874f0",
            "buy_url": f"https://www.flipkart.com/search?q={encoded_query}&affid={FLIPKART_AFF_ID}"
        },
        {
            "platform": "Croma (Tata)",
            "title": f"{query.title()} on Croma Electronics",
            "price": "Check Tata Offers",
            "numeric_price": 102,
            "badge_color": "#00b5b8",
            "buy_url": f"https://www.croma.com/searchB?q={encoded_query}"
        },
        {
            "platform": "Reliance Digital",
            "title": f"{query.title()} on Reliance Digital",
            "price": "Check Instant Cashback",
            "numeric_price": 103,
            "badge_color": "#e42529",
            "buy_url": f"https://www.reliancedigital.in/search?q={encoded_query}"
        },
        {
            "platform": "Ajio (Reliance)",
            "title": f"{query.title()} on Ajio Trends",
            "price": "Check Coupon Discount",
            "numeric_price": 104,
            "badge_color": "#2c4152",
            "buy_url": f"https://www.ajio.com/search/?text={encoded_query}"
        },
        {
            "platform": "Myntra",
            "title": f"{query.title()} on Myntra Fashion",
            "price": "Check Brand Deals",
            "numeric_price": 105,
            "badge_color": "#ff3f6c",
            "buy_url": f"https://www.myntra.com/{encoded_query}"
        },
        {
            "platform": "Tata CLiQ",
            "title": f"{query.title()} on Tata CLiQ Luxury/Mall",
            "price": "Check Official Warranty",
            "numeric_price": 106,
            "badge_color": "#212121",
            "buy_url": f"https://www.tatacliq.com/search/?searchCategory=all&text={encoded_query}"
        }
    ]
    return deals