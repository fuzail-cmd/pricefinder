import urllib.parse

def fetch_all_deals(query):
    clean_q = query.strip()
    if not clean_q:
        return []

    encoded = urllib.parse.quote_plus(clean_q)
    title = clean_q.title()

    # Direct store comparisons (Never crashes, instant response)
    deals = [
        {
            "store": "Amazon",
            "title": f"{title} (Official Amazon Store)",
            "price_raw": "Check Lowest Price",
            "image": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=300&q=80",
            "affiliate_url": f"https://www.amazon.in/s?k={encoded}"
        },
        {
            "store": "Flipkart",
            "title": f"{title} (Special Discount Deal)",
            "price_raw": "Check Best Offer",
            "image": "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=300&q=80",
            "affiliate_url": f"https://www.flipkart.com/search?q={encoded}"
        },
        {
            "store": "Amazon",
            "title": f"{title} Accessories & Cases",
            "price_raw": "View Deals",
            "image": "https://images.unsplash.com/photo-1584438784894-089d6a62b8fa?w=300&q=80",
            "affiliate_url": f"https://www.amazon.in/s?k={encoded}+cover"
        },
        {
            "store": "Flipkart",
            "title": f"{title} Combo Offers",
            "price_raw": "View Offers",
            "image": "https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=300&q=80",
            "affiliate_url": f"https://www.flipkart.com/search?q={encoded}+combo"
        }
    ]

    return deals
    
