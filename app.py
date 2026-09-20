import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.middleware.proxy_fix import ProxyFix
from authlib.integrations.flask_client import OAuth

# Insecure transport enable (OAuth proxy callback error fix)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.environ.get("SECRET_KEY", "pricedekho_secure_session_key_2026")

# Database Setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pricedekho.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'home'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    coins = db.Column(db.Integer, default=50)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Google OAuth Setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='295721596971-1j2b80snao65uu2g5fb634upm6rg32m7.apps.googleusercontent.com',
    client_secret='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',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

# Smart Search & Fallback Engine
CATALOG = [
    {
        "keywords": ["iphone 15", "iphone15", "apple iphone 15"],
        "title": "Apple iPhone 15 (128 GB) - Black",
        "amazon_price": "₹65,999",
        "flipkart_price": "₹64,999",
        "image": "https://m.media-amazon.com/images/I/71657TiFeHL._SL1500_.jpg",
        "amazon_link": "https://www.amazon.in/s?k=iphone+15",
        "flipkart_link": "https://www.flipkart.com/search?q=iphone+15"
    },
    {
        "keywords": ["samsung s24", "s24", "galaxy s24"],
        "title": "Samsung Galaxy S24 5G (Onyx Black, 8GB RAM, 128GB)",
        "amazon_price": "₹62,499",
        "flipkart_price": "₹63,999",
        "image": "https://m.media-amazon.com/images/I/71RVu88nx6L._SL1500_.jpg",
        "amazon_link": "https://www.amazon.in/s?k=samsung+s24",
        "flipkart_link": "https://www.flipkart.com/search?q=samsung+s24"
    },
    {
        "keywords": ["oneplus 12", "oneplus 12r", "12r"],
        "title": "OnePlus 12R (Cool Blue, 8GB RAM, 128GB Storage)",
        "amazon_price": "₹39,999",
        "flipkart_price": "₹38,890",
        "image": "https://m.media-amazon.com/images/I/717Qo4MH97L._SL1500_.jpg",
        "amazon_link": "https://www.amazon.in/s?k=oneplus+12r",
        "flipkart_link": "https://www.flipkart.com/search?q=oneplus+12r"
    },
    {
        "keywords": ["redmi note 13", "note 13", "redmi"],
        "title": "Redmi Note 13 5G (Prism Gold, 6GB RAM, 128GB)",
        "amazon_price": "₹16,999",
        "flipkart_price": "₹16,499",
        "image": "https://m.media-amazon.com/images/I/71VW8LmqqPL._SL1500_.jpg",
        "amazon_link": "https://www.amazon.in/s?k=redmi+note+13",
        "flipkart_link": "https://www.flipkart.com/search?q=redmi+note+13"
    },
    {
        "keywords": ["realme 12", "realme"],
        "title": "realme 12 Pro 5G (Submarine Blue, 8GB RAM, 128GB)",
        "amazon_price": "₹22,999",
        "flipkart_price": "₹21,999",
        "image": "https://m.media-amazon.com/images/I/71ybt5vUbhL._SL1500_.jpg",
        "amazon_link": "https://www.amazon.in/s?k=realme+12+pro",
        "flipkart_link": "https://www.flipkart.com/search?q=realme+12+pro"
    }
]

def search_products(query):
    deals = []
    q = query.lower()
    for item in CATALOG:
        if any(k in q for k in item["keywords"]) or any(word in item["title"].lower() for word in q.split()):
            deals.append({
                "store": "Amazon",
                "title": item["title"],
                "price": item["amazon_price"],
                "image": item["image"],
                "link": item["amazon_link"]
            })
            deals.append({
                "store": "Flipkart",
                "title": item["title"],
                "price": item["flipkart_price"],
                "image": item["image"],
                "link": item["flipkart_link"]
            })

    if not deals:
        deals.append({
            "store": "Amazon",
            "title": f"{query.title()} (Best Online Price & Offers)",
            "price": "Check Best Deal",
            "image": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400",
            "link": f"https://www.amazon.in/s?k={requests.utils.quote(query)}"
        })
        deals.append({
            "store": "Flipkart",
            "title": f"{query.title()} (Discounts & Bank Offers)",
            "price": "Check Best Deal",
            "image": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400",
            "link": f"https://www.flipkart.com/search?q={requests.utils.quote(query)}"
        })

    return deals

@app.route('/', methods=['GET', 'POST'])
def home():
    deals = []
    query = ""
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        if query:
            deals = search_products(query)
            if current_user.is_authenticated:
                current_user.coins += 5
                db.session.commit()
    return render_template('index.html', deals=deals, query=query)

@app.route('/login')
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return redirect(url_for('google_login'))

@app.route('/login/google')
def google_login():
    redirect_uri = url_for('google_authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/login/google/callback')
def google_authorize():
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        if not user_info:
            user_info = google.userinfo()
        
        email = user_info.get('email')
        name = user_info.get('name', 'User')

        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                name=name,
                email=email,
                password="GOOGLE_AUTH_SECURE",
                coins=50
            )
            db.session.add(user)
            db.session.commit()

        login_user(user)
        return redirect(url_for('home'))
    except Exception as e:
        print("OAuth Error:", e)
        return redirect(url_for('home'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
