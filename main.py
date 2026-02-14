import yfinance as yf
import os, requests, smtplib
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ---
SENDER_EMAIL = "tony55551@gmail.com"

def get_discovery_pool():
    """AI Discovery: High-growth stocks to scan for multibagger potential."""
    return [
        "KAYNES.NS", "TEJASNET.NS", "TATAELXSI.NS", "DIXON.NS", "ASMTEC.NS",
        "ASTERDM.NS", "APOLLOHOSP.NS", "MAXHEALTH.NS", "FORTIS.NS", "SYNGENE.NS",
        "MAZDOCK.NS", "RVNL.NS", "HAL.NS", "BEL.NS", "TITAGARH.NS", "IRFC.NS",
        "TATAPOWER.NS", "SJVN.NS", "SUZLON.NS", "NHPC.NS", "KPIGREEN.NS"
    ]

# --- 2. CORE UTILITIES ---
def get_relevant_news(ticker, name):
    """
    Tri-Stage News Logic: 
    1. Financial Triggers -> 2. Market Sentiment -> 3. General Mentions.
    """
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key: return "⚠️ NewsAPI Key Missing in Secrets"
    
    core_name = name.split(" ")[0]
    ticker_clean = ticker.split(".")[0]
    
    # Define search stages from specific to broad
    queries = [
        f'("{core_name}" OR "{ticker_clean}") AND (stock OR "order book" OR results OR breakout OR contract)',
        f'("{core_name}" OR "{ticker_clean}") AND (market OR "target price" OR investment)',
        f'"{core_name}"'
    ]
    
    try:
        for q in queries:
            url = f"https://newsapi.org/v2/everything?q={q}&sortBy=relevancy&language=en&apiKey={api_key}"
            response = requests.get(url).json()
            articles = response.get('articles', [])
            if articles:
                art = articles[0]
                return f"🔥 <b>{art.get('title')}</b><br><a href='{art.get('url')}'>Read Source</a>"
        
        return "Neutral catalyst: No major news in the last 48h."
    except:
        return "Intelligence feed currently offline."

def get_stock_intel(ticker, is_discovery=False):
    """Trend & Value Predictor: Identifies Golden Crosses & Value Plays."""
    try:
        stock = yf.Ticker(ticker)
        inf = stock.info
        hist = stock.history(period="1y")
        if hist.empty: return None
        
        price = inf.get('currentPrice', 0)
        
        # Trend: Golden Cross (50-day crossing above 200-day)
        ma50 = hist['Close'].rolling(50).mean().iloc[-1]
        ma200 = hist['Close'].rolling(200).mean().iloc[-1]
        is_breakout = ma50 > ma200 and price > ma50
        
        # Fundamentals: PE Logic
        pe = inf.get('trailingPE')
        is_value = isinstance(pe, (int, float)) and pe < 25

        # AI Discovery Filter: Only show if it hits a trigger
        if is_discovery and not (is_breakout or is_value):
            return None

        return {
            "name": inf.get('longName', ticker),
            "ticker": ticker,
            "sector": inf.get('sector', 'Other'),
            "price": f"₹{price:.2f}",
            "pe": pe if pe else 'N/A',
            "change": inf.get('regularMarketChangePercent', 0),
            "trend": "🚀 BULLISH (Golden Cross)" if is_breakout else "⚖️ CONSOLIDATING",
            "tag": "AI DISCOVERY" if is_discovery else "WATCHLIST",
            "news": get_relevant_news(ticker, inf.get('longName', ticker))
        }
    except: return None

# --- 3. MAIN PIPELINE ---
def main():
    with open('watchlist.txt', 'r') as f:
        watchlist_tickers = [line.strip() for line in f if line.strip()]
    
    watchlist_data = [get_stock_intel(t) for t in watchlist_tickers]
    discovery_data = [get_stock_intel(t, is_discovery=True) for t in get_discovery_pool() if t not in watchlist_tickers]
    all_data = [r for r in (watchlist_data + discovery_data) if r]

    # Advance/Decline Sentiment Calculation
    adv = len([r for r in all_data if r['change'] > 0])
    dec = len([r for r in all_data if r['change'] < 0])
    adr = adv / dec if dec > 0 else adv
    sentiment = "NEUTRAL"
    if adr > 2.0: sentiment = "EXTREME GREED"
    elif adr > 1.2: sentiment = "GREED"
    elif adr < 0.5: sentiment = "EXTREME FEAR"
    elif adr < 0.8: sentiment = "FEAR"

    # Sector Leaderboard
    sec_perf = {}
    for r in all_data:
        sec_perf.setdefault(r['sector'], []).append(r['change'])
    leaderboard = sorted([{"s": s, "avg": sum(p)/len(p)} for s, p in sec_perf.items()], key=lambda x: x['avg'], reverse=True)

    # --- 4. HTML ASSEMBLY ---
    html = f"<html><body style='background:#f4f7f6; padding:20px; font-family:sans-serif;'>"
    
    # Sentiment Meter Card
    s_col = {"EXTREME GREED": "#c0392b", "GREED": "#e67e22", "NEUTRAL": "#7f8c8d", "FEAR": "#2980b9", "EXTREME FEAR": "#27ae60"}[sentiment]
    html += f"""<div style="background:{s_col}; color:white; padding:25px; border-radius:15px; text-align:center; margin-bottom:25px;">
        <h1 style="margin:0;">MARKET SENTIMENT: {sentiment}</h1>
        <p style="margin:10px 0 0;">Advance/Decline Ratio: {adr:.2f}</p>
    </div>"""

    # Sector Leaderboard
    html += "<div style='background:#2c3e50; color:white; padding:15px; border-radius:12px; margin:20px 0;'><h3>📊 Sector Momentum Leaderboard</h3>"
    for e in leaderboard:
        html += f"<p>{e['s']}: <b style='color:{'#27ae60' if e['avg'] > 0 else '#e74c3c'};'>{e['avg']:+.2f}%</b></p>"
    html += "</div>"

    # Stock Cards by Sector
    for l_entry in leaderboard:
        sec = l_entry['s']
        html += f"<h2 style='color:#2c3e50; border-bottom:3px solid #3498db; margin-top:40px;'>📂 {sec}</h2>"
        for r in [x for x in all_data if x['sector'] == sec]:
            tag_col = "#9b59b6" if r['tag'] == "AI DISCOVERY" else "#3498db"
            html += f"""
            <div style="background:white; border-radius:15px; padding:20px; margin-bottom:20px; border:1px solid #ddd; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #eee; padding-bottom:10px; margin-bottom:10px;">
                    <span style="font-size:1.3em; font-weight:bold;">{r['name']} <span style="background:{tag_col}; color:white; font-size:10px; padding:3px 8px; border-radius:4px; vertical-align:middle;">{r['tag']}</span></span>
                    <span style="color:{'#27ae60' if 'BULLISH' in r['trend'] else '#7f8c8d'}; font-weight:bold;">{r['trend']}</span>
                </div>
                <div style="margin:12px 0; font-size:0.95em;">Price: <b>{r['price']}</b> ({r['change']:+.2f}%) | PE: {r['pe']}</div>
                <div style="background:#f8f9fa; padding:15px; border-radius:10px; border-left:4px solid #3498db;">{r['news']}</div>
            </div>"""

    html += "</body></html>"
    
    # Send Email
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL; msg['To'] = SENDER_EMAIL
    msg['Subject'] = f"🚀 Pro AI Market Intelligence: {datetime.now().strftime('%d %b %Y')}"
    msg.attach(MIMEText(html, 'html'))
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
        srv.login(SENDER_EMAIL, os.getenv("EMAIL_PASS"))
        srv.send_message(msg)

if __name__ == "__main__":
    main()
