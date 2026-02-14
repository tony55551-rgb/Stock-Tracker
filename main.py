import yfinance as yf
import os, requests, smtplib, base64, io
import mplfinance as mpf
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

SENDER_EMAIL = "tony55551@gmail.com"

def get_discovery_picks():
    """AI Screener: Hunts for emerging mid/small caps in high-growth sectors."""
    # List of high-growth sectors to scan (Defense, Rail, 5G, Green Energy)
    discovery_pool = [
        "MAZDOCK.NS", "RVNL.NS", "TEJASNET.NS", "HAL.NS", "BEL.NS", 
        "TITAGARH.NS", "IRFC.NS", "SJVN.NS", "SUZLON.NS", "KAYNES.NS",
        "GPTINFRA.NS", "RELIANCE.NS", "ASHOKLEY.NS", "DATA-PATTERNS.NS"
    ]
    picks = []
    for ticker in discovery_pool:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            ma50 = hist['Close'].rolling(50).mean().iloc[-1]
            ma200 = hist['Close'].rolling(200).mean().iloc[-1]
            price = hist['Close'].iloc[-1]
            pe = stock.info.get('trailingPE', 100)
            
            # TRIGGER: Golden Cross OR Undervalued (PE < 20)
            if (ma50 > ma200 and price > ma50) or (pe < 20):
                picks.append(ticker)
        except: continue
    return picks

def get_relevant_news(ticker, name):
    """Boolean Search: Anchors news to financial catalysts only."""
    api_key = os.getenv("NEWS_API_KEY")
    # Query: ("Company" OR "Ticker") AND (Financial Triggers) NOT (General Noise)
    core_name = name.split(" ")[0]
    query = f'("{core_name}" OR "{ticker.split(".")[0]}") AND ("order book" OR "L1 bidder" OR "results" OR "breakout") -jobs -hiring'
    url = f"https://newsapi.org/v2/everything?q={query}&sortBy=relevancy&language=en&apiKey={api_key}"
    try:
        art = requests.get(url).json().get('articles', [{}])[0]
        return f"🔥 <b>{art.get('title')}</b><br><a href='{art.get('url')}'>Source</a>" if art.get('title') else "Neutral news flow."
    except: return "Intelligence feed offline."

def get_stock_card(ticker, is_discovery=False):
    try:
        stock = yf.Ticker(ticker)
        inf = stock.info
        hist = stock.history(period="6mo")
        price = inf.get('currentPrice', 0)
        
        # Professional Charting
        buf = io.BytesIO()
        mc = mpf.make_marketcolors(up='#27ae60', down='#c0392b', inherit=True)
        s = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
        hlines = dict(hlines=[hist['Low'].min(), hist['High'].max()], colors=['#2980b9', '#e67e22'], linestyle='-.', linewidths=1.5)
        mpf.plot(hist, type='candle', style=s, hlines=hlines, mav=(50, 200), savefig=dict(fname=buf, format='png', dpi=100))
        buf.seek(0)
        chart_b64 = base64.b64encode(buf.read()).decode('utf-8')

        tag = "DISCOVERY" if is_discovery else "WATCHLIST"
        color = "#9b59b6" if is_discovery else "#3498db"
        
        return f"""
        <div style="background:white; border-radius:15px; padding:20px; margin-bottom:25px; border:1px solid #ddd;">
            <div style="display:flex; justify-content:space-between;">
                <span style="font-size:1.3em; font-weight:bold;">{inf.get('longName', ticker)}</span>
                <span style="background:{color}; color:white; padding:2px 8px; border-radius:4px; font-size:10px;">{tag}</span>
            </div>
            <div style="margin:10px 0; font-size:0.9em;">Price: <b>₹{price:.2f}</b> | PE: {inf.get('trailingPE', 'N/A')} | Sector: {inf.get('sector', 'N/A')}</div>
            <img src="data:image/png;base64,{chart_b64}" style="width:100%; border-radius:8px;">
            <div style="background:#f8f9fa; padding:12px; border-radius:8px; margin-top:10px; font-size:0.85em;">{get_relevant_news(ticker, inf.get('longName', ticker))}</div>
        </div>"""
    except: return ""

def main():
    # 1. Load your static watchlist
    with open('watchlist.txt', 'r') as f:
        watchlist = [line.strip() for line in f if line.strip()]
    
    # 2. Automatically discover new potential stocks
    discovery_list = get_discovery_picks()
    
    html = f"<html><body style='background:#f4f7f6; padding:20px; font-family:sans-serif;'>"
    html += "<h1 style='text-align:center;'>Institutional Intelligence Report</h1>"
    
    # Process Watchlist
    for s in watchlist: html += get_stock_card(s, is_discovery=False)
    
    # Process Discovery (Only if not already in watchlist)
    new_picks = [s for s in discovery_list if s not in watchlist]
    if new_picks:
        html += "<h2 style='color:#9b59b6; border-bottom:2px solid #9b59b6;'>✨ AI Discoveries (High Potential)</h2>"
        for s in new_picks: html += get_stock_card(s, is_discovery=True)

    html += "</body></html>"
    
    msg = MIMEMultipart(); msg['From'] = SENDER_EMAIL; msg['To'] = SENDER_EMAIL
    msg['Subject'] = f"🚀 Market Intelligence: {len(watchlist)} Tracked | {len(new_picks)} Discovered"
    msg.attach(MIMEText(html, 'html'))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
        srv.login(SENDER_EMAIL, os.getenv("EMAIL_PASS")); srv.send_message(msg)

if __name__ == "__main__": main()
