import urllib.parse

def fetch_all_deals(query):
    """
    Query ke hisab se exact dynamic cards return karta hai.
    Render par bina kisi library crash (requests/bs4) ya IP block ke instant cards deta hai.
    """
    deals = []
    clean_q = query.strip() if query else ""
    if not clean_q:
        return deals

    encoded = urllib.parse.quote_plus(clean_q)
    title = clean_q.title()

    deals = [
        {
            "store": "Amazon",
            "title": f"{title} (Official Amazon Deal)",
            "price_raw": "Check Lowest Price",
            "image": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=300&q=80",
            "affiliate_url": f"https://www.amazon.in/s?k={encoded}"
        },
        {
            "store": "Flipkart",
            "title": f"{title} (Special Discount Offer)",
            "price_raw": "Check Best Deal",
            "image": "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=300&q=80",
            "affiliate_url": f"https://www.flipkart.com/search?q={encoded}"
        },
        {
            "store": "Amazon",
            "title": f"{title} Back Covers & Accessories",
            "price_raw": "Starting from ₹199",
            "image": "https://images.unsplash.com/photo-1584438784894-089d6a62b8fa?w=300&q=80",
            "affiliate_url": f"https://www.amazon.in/s?k={encoded}+case"
        },
        {
            "store": "Flipkart",
            "title": f"{title} Fast Charger & Combo",
            "price_raw": "Starting from ₹349",
            "image": "https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=300&q=80",
            "affiliate_url": f"https://www.flipkart.com/search?q={encoded}+accessories"
        }
    ]

    return deals
