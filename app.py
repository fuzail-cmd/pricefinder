import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.middleware.proxy_fix import ProxyFix
from authlib.integrations.flask_client import OAuth

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

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    profile_pic = db.Column(db.String(500), nullable=True, default="")
    coins = db.Column(db.Integer, default=50)
    country_code = db.Column(db.String(10), nullable=True, default="+91")
    phone = db.Column(db.String(20), nullable=True, default="")
    upi_id = db.Column(db.String(100), nullable=True, default="")
    bank_account = db.Column(db.String(50), nullable=True, default="")
    bank_ifsc = db.Column(db.String(30), nullable=True, default="")

    def completion_percentage(self):
        score = 0
        # 1. Profile Picture
        if self.profile_pic and "flaticon" not in self.profile_pic:
            score += 20
        # 2. Full Name
        if self.name and len(self.name.strip()) > 2:
            score += 20
        # 3. Mobile Number (10 digits)
        if self.phone and len(self.phone.strip()) >= 10:
            score += 20
        # 4. UPI ID
        if self.upi_id and "@" in self.upi_id:
            score += 20
        # 5. Bank Details
        if self.bank_account and self.bank_ifsc:
            score += 20
        return score

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

# Product Fallback Catalog
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

# Profile Update Route (Save 5 Fields)
@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    name = request.form.get('name', '').strip()
    profile_pic = request.form.get('profile_pic', '').strip()
    country_code = request.form.get('country_code', '+91').strip()
    phone = request.form.get('phone', '').strip()
    upi_id = request.form.get('upi_id', '').strip()
    bank_account = request.form.get('bank_account', '').strip()
    bank_ifsc = request.form.get('bank_ifsc', '').strip()

    if name:
        current_user.name = name
    if profile_pic:
        current_user.profile_pic = profile_pic
    current_user.country_code = country_code
    current_user.phone = phone
    current_user.upi_id = upi_id
    current_user.bank_account = bank_account
    current_user.bank_ifsc = bank_ifsc

    db.session.commit()
    return redirect(url_for('home'))

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
        picture = user_info.get('picture', 'https://cdn-icons-png.flaticon.com/512/3177/3177440.png')

        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                name=name,
                email=email,
                password="GOOGLE_AUTH_SECURE",
                profile_pic=picture,
                coins=50
            )
            db.session.add(user)
            db.session.commit()
        else:
            if not user.profile_pic or "flaticon" in user.profile_pic:
                user.profile_pic = picture
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

# Admin Dashboard
@app.route('/admin/users')
def view_users():
    secret_key = request.args.get('key')
    if secret_key != "pricedekho_admin_99":
        return "Access Denied: Invalid Key", 403

    users = User.query.all()
    total = len(users)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PriceDekho Admin - Users List</title>
        <style>
            body {{ font-family: sans-serif; padding: 24px; background: #f8fafc; color: #0f172a; }}
            h2 {{ margin-bottom: 8px; }}
            .badge {{ background: #2563eb; color: white; padding: 4px 10px; border-radius: 12px; font-size: 14px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 16px; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            th, td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid #e2e8f0; font-size: 13px; vertical-align: middle; }}
            th {{ background: #f1f5f9; font-weight: 700; }}
            tr:hover {{ background: #f8fafc; }}
            .avatar {{ width: 34px; height: 34px; border-radius: 50%; object-fit: cover; border: 1px solid #cbd5e1; }}
        </style>
    </head>
    <body>
        <h2>Registered Users <span class="badge">Total: {total}</span></h2>
        <table>
            <tr>
                <th>Photo</th>
                <th>Name</th>
                <th>Email</th>
                <th>Mobile Number</th>
                <th>UPI ID</th>
                <th>Bank A/C & IFSC</th>
                <th>Profile Status</th>
                <th>Coins</th>
            </tr>
    """

    for u in users:
        pic = u.profile_pic if u.profile_pic else "https://cdn-icons-png.flaticon.com/512/3177/3177440.png"
        code = u.country_code or "+91"
        phone_txt = f"{code} {u.phone}" if u.phone else "<span style='color:#94a3b8;'>Not added</span>"
        upi_disp = u.upi_id if u.upi_id else "<span style='color:#94a3b8;'>Not added</span>"
        bank_disp = f"{u.bank_account} ({u.bank_ifsc})" if (u.bank_account or u.bank_ifsc) else "<span style='color:#94a3b8;'>Not added</span>"
        perc = u.completion_percentage()
        status_tag = f"<span style='color:#16a34a;font-weight:700;'>✔ Completed</span>" if perc == 100 else f"<span style='color:#ea580c;font-weight:700;'>{perc}% Filled</span>"

        html += f"""
            <tr>
                <td><img src="{pic}" class="avatar" alt="Avatar"></td>
                <td><strong>{u.name}</strong></td>
                <td>{u.email}</td>
                <td><strong>{phone_txt}</strong></td>
                <td><code>{upi_disp}</code></td>
                <td>{bank_disp}</td>
                <td>{status_tag}</td>
                <td>🪙 <strong>{u.coins}</strong></td>
            </tr>
        """

    html += """
        </table>
    </body>
    </html>
    """
    return html

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
