import os
import requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.middleware.proxy_fix import ProxyFix
from authlib.integrations.flask_client import OAuth

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.environ.get("SECRET_KEY", "pricedekho_secure_production_secret_2026")

# Database Setup
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'pricedekho.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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
    coins = db.Column(db.Integer, default=50)
    country_code = db.Column(db.String(10), nullable=True, default="+91")
    phone = db.Column(db.String(20), nullable=True, default="")
    upi_id = db.Column(db.String(100), nullable=True, default="")
    bank_account = db.Column(db.String(50), nullable=True, default="")
    bank_ifsc = db.Column(db.String(30), nullable=True, default="")
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

# Earning History Model
class Transaction(db.Model):
    __tablename__ = 'transaction'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    coins = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Payout Request Model (₹50 Minimum Payout)
class PayoutRequest(db.Model):
    __tablename__ = 'payout_request'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount_inr = db.Column(db.Integer, default=50)
    coins_deducted = db.Column(db.Integer, default=500)
    payment_method = db.Column(db.String(100), nullable=False) # e.g. UPI or Bank
    status = db.Column(db.String(20), default="Pending") # Pending, Completed, Rejected
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
            history = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.timestamp.desc()).limit(15).all()
            # Pending Payout Check
            pending_payout = PayoutRequest.query.filter_by(user_id=current_user.id, status="Pending").order_by(PayoutRequest.timestamp.desc()).first()
            # Last Successful Payment Check
            last_payout = PayoutRequest.query.filter_by(user_id=current_user.id, status="Completed").order_by(PayoutRequest.completed_at.desc()).first()
        except Exception:
            db.session.rollback()

    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        if query:
            deals = search_products(query)
            if current_user.is_authenticated:
                try:
                    current_user.coins += 5
                    tx = Transaction(user_id=current_user.id, title=f"Searched: {query}", coins=5)
                    db.session.add(tx)
                    db.session.commit()
                    history = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.timestamp.desc()).limit(15).all()
                except Exception:
                    db.session.rollback()

    return render_template('index.html', deals=deals, query=query, history=history, pending_payout=pending_payout, last_payout=last_payout)

# API: Watch Ad
@app.route('/api/claim-ad-reward', methods=['POST'])
@login_required
def claim_ad_reward():
    try:
        current_user.coins += 10
        tx = Transaction(user_id=current_user.id, title="Watched Video / Sponsor Ad", coins=10)
        db.session.add(tx)
        db.session.commit()
        return jsonify({"success": True, "coins": current_user.coins, "reward": 10})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

# API: Complete Task
@app.route('/api/complete-task', methods=['POST'])
@login_required
def complete_task():
    try:
        data = request.get_json() or {}
        task_name = data.get('task_name', 'Task Bonus')
        reward_coins = int(data.get('reward', 25))

        current_user.coins += reward_coins
        tx = Transaction(user_id=current_user.id, title=f"Completed Task: {task_name}", coins=reward_coins)
        db.session.add(tx)
        db.session.commit()
        return jsonify({"success": True, "coins": current_user.coins, "reward": reward_coins})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

# API: Request Payout (₹50 Minimum Rule: 500 Coins = ₹50)
@app.route('/api/request-payout', methods=['POST'])
@login_required
def request_payout():
    try:
        # Check if already has a pending request
        existing = PayoutRequest.query.filter_by(user_id=current_user.id, status="Pending").first()
        if existing:
            return jsonify({"success": False, "message": "Aapki pichli ₹50 payout request already Pending/Processing me hai!"}), 400

        # Check Minimum Coins requirement: 500 coins = ₹50
        if current_user.coins < 500:
            remaining = 500 - current_user.coins
            return jsonify({"success": False, "message": f"Minimum payout ₹50 ke liye 500 coins chahiye. Aapko aur {remaining} coins earn karne honge!"}), 400

        # Check Payment Method Added
        p_method = current_user.upi_id if current_user.upi_id else f"{current_user.bank_account} ({current_user.bank_ifsc})"
        if not current_user.upi_id and not current_user.bank_account:
            return jsonify({"success": False, "message": "Kripya payout lene se pehle apni profile me UPI ID ya Bank details add karein!"}), 400

        # Deduct 500 Coins and create Payout Request
        current_user.coins -= 500
        req = PayoutRequest(user_id=current_user.id, amount_inr=50, coins_deducted=500, payment_method=p_method, status="Pending")
        tx = Transaction(user_id=current_user.id, title="Payout Request Submitted (₹50)", coins=-500)
        
        db.session.add(req)
        db.session.add(tx)
        db.session.commit()

        return jsonify({"success": True, "message": "₹50 payout request successfully submit ho gayi hai! 24 ghante ke andar transfer ho jayegi."})
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

        tx = Transaction(user_id=current_user.id, title="Profile KYC Updated", coins=0)
        db.session.add(tx)
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
            
            welcome_tx = Transaction(user_id=user.id, title="Welcome Sign Up Bonus", coins=50)
            db.session.add(welcome_tx)
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

# Admin Dashboard with Payout Management
@app.route('/admin/users')
def view_users():
    secret_key = request.args.get('key')
    if secret_key != "pricedekho_admin_99":
        return "Access Denied: Invalid Key", 403

    # Handle Admin Payout Approval Action: /admin/users?key=pricedekho_admin_99&approve_payout=1
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
        <title>PriceDekho Admin - Payouts & Users</title>
        <style>
            body {{ font-family: -apple-system, sans-serif; padding: 24px; background: #f8fafc; color: #0f172a; }}
            h2 {{ margin-bottom: 8px; }}
            .badge {{ background: #2563eb; color: white; padding: 4px 10px; border-radius: 12px; font-size: 14px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 14px; margin-bottom: 30px; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            th, td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid #e2e8f0; font-size: 13px; vertical-align: middle; }}
            th {{ background: #f1f5f9; font-weight: 700; }}
            tr:hover {{ background: #f8fafc; }}
            .avatar {{ width: 34px; height: 34px; border-radius: 50%; object-fit: cover; border: 1px solid #cbd5e1; }}
            .btn-pay {{ background: #16a34a; color: white; padding: 6px 12px; border-radius: 6px; text-decoration: none; font-weight: 700; font-size: 12px; }}
            .btn-pay:hover {{ background: #15803d; }}
            .status-pending {{ color: #ea580c; font-weight: 700; background: #ffedd5; padding: 3px 8px; border-radius: 6px; }}
            .status-paid {{ color: #16a34a; font-weight: 700; background: #dcfce7; padding: 3px 8px; border-radius: 6px; }}
        </style>
    </head>
    <body>
        <h2>💸 Payout Requests (₹50 Withdrawals)</h2>
        <table>
            <tr>
                <th>Req ID</th>
                <th>User</th>
                <th>Amount</th>
                <th>Payment Destination (UPI / Bank)</th>
                <th>Date</th>
                <th>Status</th>
                <th>Action</th>
            </tr>
    """

    if not payout_requests:
        html += "<tr><td colspan='7' style='text-align:center; color:#94a3b8; padding:16px;'>No payout requests yet.</td></tr>"
    else:
        for p in payout_requests:
            act = f"<a href='/admin/users?key=pricedekho_admin_99&approve_payout={p.id}' class='btn-pay'>✔ Mark as Paid</a>" if p.status == 'Pending' else "<span style='color:#16a34a; font-weight:bold;'>Paid & Closed</span>"
            st_class = "status-pending" if p.status == 'Pending' else "status-paid"
            html += f"""
                <tr>
                    <td>#{p.id}</td>
                    <td><strong>{p.user.name}</strong> ({p.user.email})</td>
                    <td><strong>₹{p.amount_inr}</strong> (500 Coins)</td>
                    <td><code>{p.payment_method}</code></td>
                    <td>{p.timestamp.strftime('%d %b %Y, %I:%M %p')}</td>
                    <td><span class='{st_class}'>{p.status}</span></td>
                    <td>{act}</td>
                </tr>
            """

    html += f"""
        </table>

        <h2>👥 Registered Users <span class="badge">Total: {len(users)}</span></h2>
        <table>
            <tr>
                <th>Photo</th>
                <th>Name</th>
                <th>Email</th>
                <th>Mobile</th>
                <th>UPI ID</th>
                <th>Bank Info</th>
                <th>Profile Status</th>
                <th>Coins Balance</th>
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
                <td>🪙 <strong>{u.coins}</strong> (≈ ₹{u.coins/10})</td>
            </tr>
        """

    html += """
        </table>
    </body>
    </html>
    """
    return html

# Automatic Database Migration / Column Injection
with app.app_context():
    db.create_all()
    try:
        with db.engine.connect() as conn:
            from sqlalchemy import text
            for col, col_type in [
                ("country_code", "VARCHAR(10) DEFAULT '+91'"),
                ("phone", "VARCHAR(20) DEFAULT ''"),
                ("upi_id", "VARCHAR(100) DEFAULT ''"),
                ("bank_account", "VARCHAR(50) DEFAULT ''"),
                ("bank_ifsc", "VARCHAR(30) DEFAULT ''"),
                ("profile_pic", "VARCHAR(500) DEFAULT ''")
            ]:
                try:
                    conn.execute(text(f"ALTER TABLE user ADD COLUMN {col} {col_type};"))
                    conn.commit()
                except Exception:
                    pass
    except Exception as e:
        print("Schema sync check:", e)

if __name__ == '__main__':
    app.run(debug=True)
