from flask import Flask, render_template, request
from scraper import fetch_all_deals

app = Flask(__name__)

@app.route('/')
def home():
    query = request.args.get('q', '').strip()
    deals = []
    if query:
        deals = fetch_all_deals(query)
    return render_template('index.html', query=query, deals=deals)

if __name__ == '__main__':
    app.run(debug=True)