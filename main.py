import yfinance as yf
import os, requests, smtplib, base64, io
import mplfinance as mpf
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

SENDER_EMAIL = "tony55551@gmail.com"

def get_discovery_pool():
    # Targeted '2x' Potential Sectors for 2026: Defense, Railway, Tech, Energy
    return ["MAZDOCK.NS", "RVNL.NS", "TEJASNET.NS", "KAYNES.NS", "TITAGARH.NS", 
            "HAL.NS", "BEL.NS", "IRFC.NS", "SJVN.NS", "SUZLON.NS", "GPTINFRA.NS"]

def get_chart_base64(ticker):
    try:
        data = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if data.empty: return ""
        # Automated Support (Blue) and Resistance (Orange)
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
    # Boolean logic to anchor search to financial catalysts
    core_name = name.split(" ")[0]
    query = f'("{core_name}" OR "{ticker.split(".")[0]}") AND (stock OR "order book" OR results OR breakout) -jobs -hiring'
    url = f"https://newsapi.org/v2/everything?q={query}&sortBy=relevancy&language=en&apiKey={api_key}"
    try:
        art = requests.get(url).json().get('articles', [{}])[0]
        return f"🔥 <b>{art.get('title')}</b><br><a href='{art.get('url')}'>Read Source</a>" if art.get('title') else "Neutral catalyst."
    except: return "Intelligence feed currently offline."

def get_stock_data(ticker, is_discovery=False):
    try:
        stock = yf.Ticker(ticker)
        inf, hist = stock.info, stock.history(period="1y")
        price = inf.get('currentPrice', 0)
        # 1. GOLDEN CROSS: 50-day average crosses 200-day average
        ma50 = hist['Close'].rolling(50).mean().iloc[-1]
        ma200 = hist['Close'].rolling(200).mean().iloc[-1]
        is_breakout = ma50 > ma200 and price > ma50
        
        # 2. VALUE FLAG: PE under 20
        pe = inf.get('trailingPE')
        is_value = isinstance(pe, (int, float)) and pe < 20
        
        # If discovery stock, only include if it hits a breakout or value trigger
        if is_discovery and not (is_breakout or is_value): return None

        return {
            "name": inf.get('longName', ticker), "sector": inf.get('sector', 'Other'),
            "price": f"₹{price:.2f}", "pe": pe if pe else 'N/A',
            "change": inf.get('regularMarketChangePercent', 0),
            "trend": "🚀 BULLISH (Golden Cross)" if is_breakout else "⚖️ CONSOLIDATING",
            "tag": "AI DISCOVERY" if is_discovery else "WATCHLIST",
            "chart": get_chart_base64(ticker), "news": get_relevant_news(ticker, inf.get('longName', ticker))
        }
    except: return None

def main():
    with open('watchlist.txt', 'r') as f:
        watchlist_tickers = [line.strip() for line in f if line.strip()]
    
    # Process both lists
    watchlist_data = [get_stock_data(t) for t in watchlist_tickers]
    discovery_data = [get_stock_data(t, is_discovery=True) for t in get_discovery_pool() if t not in watchlist_tickers]
    all_results = [r for r in (watchlist_data + discovery_data) if r]

    # 3. MARKET STRENGTH LEADERBOARD: Calculate Sector Momentum
    sector_perf = {}
    for r in all_results: sector_perf.setdefault(r['sector'], []).append(r['change'])
    leaderboard = sorted([{"s": s, "avg": sum(p)/len(p)} for s, p in sector_perf.items()], key=lambda x: x['avg'], reverse=True)

    html = f"<html><body style='background:#f4f7f6; padding:20px; font-family:sans-serif;'>"
    
    # 4. LEADERBOARD DISPLAY
    html += "<div style='background:#2c3e50; color:white; padding:20px; border-radius:12px; margin-bottom:30px;'>"
    html += "<h2>📊 Market Strength Leaderboard</h2>"
    for entry in leaderboard:
        color = "#27ae60" if entry['avg'] > 0 else "#e74c3c"
        html += f"<p>{entry['s']}: <b style='color:{color};'>{entry['avg']:+.2f}%</b></p>"
    html += "</div>"

    # 5. SECTOR-WISE CARDS
    for sector in [l['s'] for l in leaderboard]:
        html += f"<h2 style='color:#2c3e50; border-bottom:3px solid #3498db; margin-top:40px;'>📂 {sector}</h2>"
        for r in [x for x in all_results if x['sector'] == sector]:
            tag_color = "#9b59b6" if r['tag'] == "AI DISCOVERY" else "#3498db"
            html += f"""
            <div style="background:white; border-radius:15px; padding:20px; margin-bottom:25px; border:1px solid #ddd;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:1.3em; font-weight:bold;">{r['name']} <span style="background:{tag_color}; color:white; font-size:10px; padding:2px 6px; border-radius:4px;">{r['tag']}</span></span>
                    <span style="color:{'#27ae60' if 'BULLISH' in r['trend'] else '#7f8c8d'}; font-weight:bold; font-size:0.9em;">{r['trend']}</span>
                </div>
                <div style="margin:10px 0; font-size:0.9em;">Price: <b>{r['price']}</b> ({r['change']:+.2f}%) | PE: {r['pe']}</div>
                <img src="data:image/png;base64,{r['chart']}" style="width:100%; border-radius:8px;">
                <div style="background:#f8f9fa; padding:12px; border-radius:10px; margin-top:10px; font-size:0.85em;">{r['news']}</div>
            </div>"""

    html += "</body></html>"
    msg = MIMEMultipart(); msg['From'] = SENDER_EMAIL; msg['To'] = SENDER_EMAIL
    msg['Subject'] = f"🚀 Pro Market Intelligence: {datetime.now().strftime('%d %b %Y')}"
    msg.attach(MIMEText(html, 'html'))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
        srv.login(SENDER_EMAIL, os.getenv("EMAIL_PASS")); srv.send_message(msg)

if __name__ == "__main__": main()
