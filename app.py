import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "pricedekho_secure_session_key_2026")

# Database Setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pricedekho.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Login Manager Setup
login_manager = LoginManager(app)
login_manager.login_view = 'home'

# User Model
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
    access_token_url='https://oauth2.googleapis.com/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'openid email profile'},
)

# Helper Function: Amazon Scraper
def get_amazon_deals(query):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    url = f"https://www.amazon.in/s?k={query}"
    deals = []
    try:
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.content, "html.parser")
        items = soup.select('div[data-component-type="s-search-result"]')
        for item in items[:4]:
            title_elem = item.select_one("h2 a span")
            price_elem = item.select_one(".a-price-whole")
            img_elem = item.select_one(".s-image")
            link_elem = item.select_one("h2 a")

            if title_elem and price_elem:
                title = title_elem.text.strip()
                price = "₹" + price_elem.text.strip()
                image = img_elem['src'] if img_elem else "https://via.placeholder.com/150"
                link = "https://www.amazon.in" + link_elem['href']
                deals.append({
                    "store": "Amazon",
                    "title": title,
                    "price": price,
                    "image": image,
                    "link": link
                })
    except Exception as e:
        print("Amazon fetch error:", e)
    return deals

# Helper Function: Flipkart Deals
def get_flipkart_deals(query):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    url = f"https://www.flipkart.com/search?q={query}"
    deals = []
    try:
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.content, "html.parser")
        containers = soup.select('div[data-id]')
        for item in containers[:4]:
            title_elem = item.select_one(".KzDlHZ") or item.select_one(".wjcEIp")
            price_elem = item.select_one(".Nx9bqj")
            img_elem = item.select_one("img")
            link_elem = item.select_one("a")

            if title_elem and price_elem:
                title = title_elem.text.strip()
                price = price_elem.text.strip()
                image = img_elem['src'] if img_elem else "https://via.placeholder.com/150"
                raw_link = link_elem['href'] if link_elem else ""
                link = "https://www.flipkart.com" + raw_link if raw_link.startswith("/") else raw_link
                deals.append({
                    "store": "Flipkart",
                    "title": title,
                    "price": price,
                    "image": image,
                    "link": link
                })
    except Exception as e:
        print("Flipkart fetch error:", e)
    return deals

# Routes
@app.route('/', methods=['GET', 'POST'])
def home():
    deals = []
    query = ""
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        if query:
            deals.extend(get_amazon_deals(query))
            deals.extend(get_flipkart_deals(query))
            if current_user.is_authenticated:
                current_user.coins += 5
                db.session.commit()
    return render_template('index.html', deals=deals, query=query)

@app.route('/login/google')
def google_login():
    redirect_uri = url_for('google_authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/login/google/callback')
def google_authorize():
    token = google.authorize_access_token()
    user_info = google.get('userinfo').json()
    
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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
