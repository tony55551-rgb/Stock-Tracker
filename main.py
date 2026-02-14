import yfinance as yf
import os, requests, smtplib, base64, io
import mplfinance as mpf
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

SENDER_EMAIL = "tony55551@gmail.com"

def get_discovery_pool():
    # Targeted '2x' Potential Sectors for 2026
    return ["MAZDOCK.NS", "RVNL.NS", "TEJASNET.NS", "KAYNES.NS", "TITAGARH.NS", "SJVN.NS", "IRFC.NS", "DATA-PATTERNS.NS"]

def get_chart_base64(ticker):
    try:
        data = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if data.empty: return ""
        sup, res = data['Low'].min(), data['High'].max()
        buf = io.BytesIO()
        mc = mpf.make_marketcolors(up='#27ae60', down='#c0392b', inherit=True)
        s = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
        hlines = dict(hlines=[sup, res], colors=['#2980b9', '#e67e22'], linestyle='-.', linewidths=1.5)
        mpf.plot(data, type='candle', style=s, hlines=hlines, mav=(50, 200), volume=True, 
                 savefig=dict(fname=buf, format='png', dpi=100))
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')
    except: return ""

def get_relevant_news(ticker, name):
    api_key = os.getenv("NEWS_API_KEY")
    query = f'("{name.split(" ")[0]}" OR "{ticker.split(".")[0]}") AND (stock OR "order book" OR breakout OR contract) -jobs -hiring'
    url = f"https://newsapi.org/v2/everything?q={query}&sortBy=relevancy&language=en&apiKey={api_key}"
    try:
        art = requests.get(url).json().get('articles', [{}])[0]
        return f"🔥 <b>{art.get('title')}</b><br><a href='{art.get('url')}'>Source</a>" if art.get('title') else "Neutral catalyst."
    except: return "Intelligence feed offline."

def get_stock_data(ticker, is_discovery=False):
    try:
        stock = yf.Ticker(ticker)
        inf, hist = stock.info, stock.history(period="1y")
        price = inf.get('currentPrice', 0)
        ma50, ma200 = hist['Close'].rolling(50).mean().iloc[-1], hist['Close'].rolling(200).mean().iloc[-1]
        
        # Trend & Value Logic
        is_breakout = ma50 > ma200 and price > ma50
        is_value = isinstance(inf.get('trailingPE'), (int, float)) and inf.get('trailingPE') < 20
        
        # Only return Discovery stocks if they hit a trigger
        if is_discovery and not (is_breakout or is_value): return None

        return {
            "name": inf.get('longName', ticker), "sector": inf.get('sector', 'Other'),
            "price": f"₹{price:.2f}", "pe": inf.get('trailingPE', 'N/A'),
            "change": inf.get('regularMarketChangePercent', 0),
            "trend": "🚀 BULLISH BREAKOUT" if is_breakout else "⚖️ CONSOLIDATING",
            "tag": "AI DISCOVERY" if is_discovery else "WATCHLIST",
            "chart": get_chart_base64(ticker), "news": get_relevant_news(ticker, inf.get('longName', ticker))
        }
    except: return None

def main():
    with open('watchlist.txt', 'r') as f:
        watchlist = [line.strip() for line in f if line.strip()]
    
    # 1. Gather all data (Watchlist + Discovery Pool)
    results = [get_stock_data(t) for t in watchlist]
    discoveries = [get_stock_data(t, is_discovery=True) for t in get_discovery_pool() if t not in watchlist]
    all_data = [r for r in (results + discoveries) if r]

    # 2. Market Strength Leaderboard
    sector_perf = {}
    for r in all_data: sector_perf.setdefault(r['sector'], []).append(r['change'])
    leaderboard = sorted([{"s": s, "avg": sum(p)/len(p)} for s, p in sector_perf.items()], key=lambda x: x['avg'], reverse=True)

    # 3. HTML Building
    html = f"<html><body style='background:#f4f7f6; padding:20px; font-family:sans-serif;'>"
    html += "<div style='background:#2c3e50; color:white; padding:20px; border-radius:12px; margin-bottom:30px;'>"
    html += "<h2>📊 Market Strength Leaderboard</h2><table style='width:100%; color:white;'>"
    for entry in leaderboard:
        html += f"<tr><td>{entry['s']}</td><td style='text-align:right; color:{'#27ae60' if entry['avg'] > 0 else '#e74c3c'}; font-weight:bold;'>{entry['avg']:+.2f}%</td></tr>"
    html += "</table></div>"

    for sector in [l['s'] for l in leaderboard]:
        html += f"<h2 style='color:#2c3e50; border-bottom:3px solid #3498db;'>📂 {sector}</h2>"
        for r in [x for x in all_data if x['sector'] == sector]:
            color = "#9b59b6" if r['tag'] == "AI DISCOVERY" else "#3498db"
            html += f"""<div style="background:white; border-radius:15px; padding:20px; margin-bottom:25px; border:1px solid #ddd;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:1.3em; font-weight:bold;">{r['name']} <span style="background:{color}; color:white; font-size:10px; padding:2px 6px; border-radius:4px;">{r['tag']}</span></span>
                    <span style="color:{'#27ae60' if 'BULLISH' in r['trend'] else '#7f8c8d'}; font-weight:bold; font-size:0.9em;">{r['trend']}</span>
                </div>
                <div style="margin:10px 0; font-size:0.9em;">Price: <b>{r['price']}</b> | PE: {r['pe']}</div>
                <img src="data:image/png;base64,{r['chart']}" style="width:100%; border-radius:8px;">
                <div style="background:#f8f9fa; padding:12px; border-radius:10px; margin-top:10px; font-size:0.85em;">{r['news']}</div>
            </div>"""

    html += "</body></html>"
    msg = MIMEMultipart(); msg['From'] = SENDER_EMAIL; msg['To'] = SENDER_EMAIL
    msg['Subject'] = f"🚀 Pro AI Intelligence: {datetime.now().strftime('%d %b %Y')}"
    msg.attach(MIMEText(html, 'html'))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
        srv.login(SENDER_EMAIL, os.getenv("EMAIL_PASS")); srv.send_message(msg)

if __name__ == "__main__": main()
