import os
import time
import requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.middleware.proxy_fix import ProxyFix
from authlib.integrations.flask_client import OAuth

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.environ.get("SECRET_KEY", "pricedekho_secure_production_secret_2026")

# Database Setup: Permanent PostgreSQL on Render with auto-protocol conversion
database_url = os.environ.get("DATABASE_URL")
if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'pricedekho.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'home'

# User Model
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False, default="SECURE_OAUTH_PASS")
    profile_pic = db.Column(db.String(500), nullable=True, default="")
    coins = db.Column(db.Integer, default=50)  # 50 Coins = ₹0.50 Welcome
    country_code = db.Column(db.String(10), nullable=True, default="+91")
    phone = db.Column(db.String(20), nullable=True, default="")
    upi_id = db.Column(db.String(100), nullable=True, default="")
    bank_account = db.Column(db.String(50), nullable=True, default="")
    bank_ifsc = db.Column(db.String(30), nullable=True, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade="all, delete-orphan")
    payouts = db.relationship('PayoutRequest', backref='user', lazy=True, cascade="all, delete-orphan")

    def completion_percentage(self):
        score = 0
        if self.profile_pic and "flaticon" not in self.profile_pic:
            score += 20
        if self.name and len(self.name.strip()) > 2:
            score += 20
        if self.phone and len(self.phone.strip()) >= 10:
            score += 20
        if self.upi_id and "@" in self.upi_id:
            score += 20
        if self.bank_account and self.bank_ifsc:
            score += 20
        return score

# Transaction History Model
class Transaction(db.Model):
    __tablename__ = 'transaction'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    coins = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Payout Request Model (₹50 = 5,000 Coins)
class PayoutRequest(db.Model):
    __tablename__ = 'payout_request'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount_inr = db.Column(db.Integer, default=50)
    coins_deducted = db.Column(db.Integer, default=5000)
    payment_method = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default="Pending")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

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

# Product Catalog
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

# Active Ad Links
ADSTERRA_SMARTLINK = "https://www.profitableratecpmnetwork.com/xgc4zwdgbd?key=d589889fe65e6a1ddeccaa95d291585c"
MONETAG_TASK_LINK = "https://omg10.com/4/11848381"

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
    history = []
    pending_payout = None
    last_payout = None

    if current_user.is_authenticated:
        try:
            history = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.timestamp.desc()).limit(25).all()
            pending_payout = PayoutRequest.query.filter_by(user_id=current_user.id, status="Pending").order_by(PayoutRequest.timestamp.desc()).first()
            last_payout = PayoutRequest.query.filter_by(user_id=current_user.id, status="Completed").order_by(PayoutRequest.completed_at.desc()).first()
        except Exception:
            db.session.rollback()

    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        if query:
            deals = search_products(query)

    return render_template('index.html', deals=deals, query=query, history=history, pending_payout=pending_payout, last_payout=last_payout)

# 1. API: Load 15-Second Adsterra Smartlink
@app.route('/api/load-ad', methods=['GET'])
@login_required
def load_ad():
    session['ad_start_time'] = time.time()
    return jsonify({
        "available": True,
        "ad_url": ADSTERRA_SMARTLINK,
        "duration": 15
    })

# 2. API: Claim 15-Second Ad (+1 Coin)
@app.route('/api/claim-ad-reward', methods=['POST'])
@login_required
def claim_ad_reward():
    start_time = session.get('ad_start_time')
    if not start_time:
        return jsonify({"success": False, "message": "Ad session invalid. Kripya ad link open karein!"}), 400

    elapsed = time.time() - start_time
    if elapsed < 14.5:
        return jsonify({"success": False, "message": "Ad poori nahi dekhi! Pure 15 seconds wait karein."}), 400

    try:
        current_user.coins += 1
        tx = Transaction(user_id=current_user.id, title="Watched 15s Sponsored Ad", coins=1)
        db.session.add(tx)
        db.session.commit()
        session.pop('ad_start_time', None)
        return jsonify({"success": True, "coins": current_user.coins, "reward": 1})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

# 3. API: Load Monetag High-Reward Task (30 Seconds)
@app.route('/api/load-monetag-task', methods=['GET'])
@login_required
def load_monetag_task():
    session['task_start_time'] = time.time()
    return jsonify({
        "available": True,
        "task_url": MONETAG_TASK_LINK,
        "duration": 30
    })

# 4. API: Claim Monetag Task (+5 Coins)
@app.route('/api/claim-monetag-task', methods=['POST'])
@login_required
def claim_monetag_task():
    start_time = session.get('task_start_time')
    if not start_time:
        return jsonify({"success": False, "message": "Task session invalid. Kripya task open karein!"}), 400

    elapsed = time.time() - start_time
    if elapsed < 29.0:
        remaining = int(30 - elapsed)
        return jsonify({"success": False, "message": f"Task incomplete! Kripya sponsor page par {remaining}s aur interact karein."}), 400

    try:
        current_user.coins += 5
        tx = Transaction(user_id=current_user.id, title="Completed Monetag Sponsored Task (30s)", coins=5)
        db.session.add(tx)
        db.session.commit()
        session.pop('task_start_time', None)
        return jsonify({"success": True, "coins": current_user.coins, "reward": 5})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

# API: Request Payout (₹50 = 5,000 Coins)
@app.route('/api/request-payout', methods=['POST'])
@login_required
def request_payout():
    try:
        existing = PayoutRequest.query.filter_by(user_id=current_user.id, status="Pending").first()
        if existing:
            return jsonify({"success": False, "message": "Aapki pichli ₹50 payout request already Pending me hai!"}), 400

        if current_user.coins < 5000:
            remaining = 5000 - current_user.coins
            return jsonify({"success": False, "message": f"Minimum payout ₹50 ke liye 5,000 coins chahiye. Aur {remaining} coins earn karein!"}), 400

        p_method = current_user.upi_id if current_user.upi_id else f"{current_user.bank_account} ({current_user.bank_ifsc})"
        if not current_user.upi_id and not current_user.bank_account:
            return jsonify({"success": False, "message": "Payout lene se pehle UPI ID ya Bank details add karein!"}), 400

        current_user.coins -= 5000
        req = PayoutRequest(user_id=current_user.id, amount_inr=50, coins_deducted=5000, payment_method=p_method, status="Pending")
        tx = Transaction(user_id=current_user.id, title="Payout Request Submitted (₹50)", coins=-5000)
        
        db.session.add(req)
        db.session.add(tx)
        db.session.commit()

        return jsonify({"success": True, "message": "₹50 payout request submit ho gayi hai! 24 ghante me account me bhej di jayegi."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

# Profile Update Route
@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    try:
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
    except Exception:
        db.session.rollback()

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
            
            welcome_tx = Transaction(user_id=user.id, title="Welcome Sign Up Bonus (50 Coins = ₹0.50)", coins=50)
            db.session.add(welcome_tx)
            db.session.commit()
        else:
            if not user.profile_pic or "flaticon" in user.profile_pic:
                user.profile_pic = picture
                db.session.commit()

        login_user(user)
        return redirect(url_for('home'))
    except Exception:
        return redirect(url_for('home'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# Admin Panel
@app.route('/admin/users')
def view_users():
    secret_key = request.args.get('key')
    if secret_key != "pricedekho_admin_99":
        return "Access Denied: Invalid Key", 403

    approve_id = request.args.get('approve_payout')
    if approve_id:
        p_req = PayoutRequest.query.get(int(approve_id))
        if p_req and p_req.status == "Pending":
            p_req.status = "Completed"
            p_req.completed_at = datetime.utcnow()
            tx = Transaction(user_id=p_req.user_id, title=f"Payout Completed: ₹{p_req.amount_inr} transferred", coins=0)
            db.session.add(tx)
            db.session.commit()
            return redirect(url_for('view_users', key="pricedekho_admin_99"))

    users = User.query.all()
    payout_requests = PayoutRequest.query.order_by(PayoutRequest.timestamp.desc()).all()

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PriceDekho Admin - Control Center</title>
        <style>
            body {{ font-family: -apple-system, sans-serif; padding: 24px; background: #f8fafc; color: #0f172a; }}
            h2 {{ margin-bottom: 8px; margin-top: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 24px; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            th, td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid #e2e8f0; font-size: 13px; }}
            th {{ background: #f1f5f9; font-weight: 700; }}
            .btn-action {{ background: #16a34a; color: white; padding: 5px 10px; border-radius: 6px; text-decoration: none; font-weight: 700; font-size: 11px; }}
            .status-pending {{ color: #ea580c; font-weight: 700; background: #ffedd5; padding: 2px 6px; border-radius: 4px; }}
            .status-paid {{ color: #16a34a; font-weight: 700; background: #dcfce7; padding: 2px 6px; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <h2>💸 Payout Requests (₹50 Withdrawals)</h2>
        <table>
            <tr><th>ID</th><th>User</th><th>Amount</th><th>Method</th><th>Date</th><th>Status</th><th>Action</th></tr>
    """
    if not payout_requests:
        html += "<tr><td colspan='7' style='text-align:center; padding:12px; color:#94a3b8;'>No withdrawal requests yet.</td></tr>"
    else:
        for p in payout_requests:
            act = f"<a href='/admin/users?key=pricedekho_admin_99&approve_payout={p.id}' class='btn-action'>✔ Mark Paid</a>" if p.status == 'Pending' else "<span style='color:#16a34a; font-weight:bold;'>Completed</span>"
            html += f"""
                <tr>
                    <td>#{p.id}</td><td>{p.user.name} ({p.user.email})</td><td>₹{p.amount_inr}</td><td><code>{p.payment_method}</code></td>
                    <td>{p.timestamp.strftime('%d %b %Y, %I:%M %p')}</td>
                    <td><span class='status-{"pending" if p.status=="Pending" else "paid"}'>{p.status}</span></td><td>{act}</td>
                </tr>
            """

    html += f"""
        </table>

        <h2>👥 Registered Users (Total: {len(users)})</h2>
        <table>
            <tr><th>Name</th><th>Email</th><th>Phone</th><th>UPI ID</th><th>Bank Info</th><th>Coins</th><th>Balance (INR)</th></tr>
    """
    for u in users:
        bank_str = f"{u.bank_account} ({u.bank_ifsc})" if (u.bank_account or u.bank_ifsc) else "Not added"
        html += f"""
            <tr><td>{u.name}</td><td>{u.email}</td><td>{u.phone or 'None'}</td><td><code>{u.upi_id or 'None'}</code></td><td>{bank_str}</td><td>🪙 <strong>{u.coins}</strong></td><td>₹{u.coins / 100:.2f}</td></tr>
        """

    html += "</table></body></html>"
    return html

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
