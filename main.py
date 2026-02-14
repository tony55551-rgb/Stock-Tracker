import yfinance as yf
import os, requests, smtplib, base64, io
import mplfinance as mpf
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

SENDER_EMAIL = "tony55551@gmail.com"

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
    # HYPER-RELEVANT QUERY: Forces focus on financial events and excludes noise
    core_name = name.split(" ")[0]
    query = f'("{core_name}" OR "{ticker.split(".")[0]}") AND (stock OR "order book" OR results OR "target price") -jobs -hiring'
    url = f"https://newsapi.org/v2/everything?q={query}&sortBy=relevancy&language=en&apiKey={api_key}"
    try:
        art = requests.get(url).json().get('articles', [{}])[0]
        return f"🔥 <b>{art.get('title')}</b><br><a href='{art.get('url')}'>Read Source</a>" if art.get('title') else "Neutral news flow."
    except: return "Intelligence feed currently offline."

def get_stock_intel(ticker):
    try:
        stock = yf.Ticker(ticker)
        inf = stock.info
        hist = stock.history(period="1y")
        price = inf.get('currentPrice', 0)
        ma50 = hist['Close'].rolling(50).mean().iloc[-1]
        ma200 = hist['Close'].rolling(200).mean().iloc[-1]
        
        return {
            "name": inf.get('longName', ticker), "sector": inf.get('sector', 'Emerging'),
            "price": f"₹{price:.2f}", "pe": inf.get('trailingPE', 'N/A'),
            "eps": inf.get('trailingEps', 'N/A'), "change": inf.get('regularMarketChangePercent', 0),
            "trend": "🚀 BULLISH (Golden Cross)" if ma50 > ma200 and price > ma50 else "⚖️ CONSOLIDATING",
            "chart": get_chart_base64(ticker), "news": get_relevant_news(ticker, inf.get('longName', ticker))
        }
    except: return None

def main():
    with open('watchlist.txt', 'r') as f:
        tickers = [line.strip() for line in f if line.strip()]
    
    data_list = [get_stock_intel(t) for t in tickers if get_stock_intel(t)]
    sectors = sorted(list(set(d['sector'] for d in data_list)))

    summary = '<div style="background:#2c3e50; color:white; padding:15px; border-radius:10px; margin-bottom:30px;">'
    summary += '<h3>📊 Market Strength Leaderboard</h3>'
    for s in sectors:
        avg = sum(d['change'] for d in data_list if d['sector'] == s) / len([d for d in data_list if d['sector'] == s])
        summary += f'<p>{s}: <b style="color:{"#27ae60" if avg > 0 else "#e74c3c"};">{avg:+.2f}%</b></p>'
    summary += '</div>'

    body = ""
    for s in sectors:
        body += f'<h2 style="color:#2c3e50; border-bottom:2px solid #3498db;">📂 {s} Sector</h2>'
        for d in [x for x in data_list if x['sector'] == s]:
            body += f"""
            <div style="background:white; border-radius:12px; padding:20px; margin-bottom:25px; border:1px solid #ddd;">
                <div style="display:flex; justify-content:space-between; font-weight:bold;">
                    <span>{d['name']}</span> <span style="color:{'#27ae60' if 'BULLISH' in d['trend'] else '#7f8c8d'};">{d['trend']}</span>
                </div>
                <div style="margin:10px 0; font-size:0.9em;">Price: <b>{d['price']}</b> ({d['change']:+.2f}%) | PE: {d['pe']} | EPS: {d['eps']}</div>
                <img src="data:image/png;base64,{d['chart']}" style="width:100%; border-radius:8px;">
                <div style="background:#f8f9fa; padding:12px; border-radius:8px; margin-top:10px;">{d['news']}</div>
            </div>"""

    full_html = f"<html><body style='background:#f4f7f6; padding:20px; font-family:sans-serif;'>{summary}{body}</body></html>"
    msg = MIMEMultipart(); msg['From'] = SENDER_EMAIL; msg['To'] = SENDER_EMAIL
    msg['Subject'] = f"📈 Pro Intel Report: {datetime.now().strftime('%d %b %Y')}"
    msg.attach(MIMEText(full_html, 'html'))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
        srv.login(SENDER_EMAIL, os.getenv("EMAIL_PASS")); srv.send_message(msg)

if __name__ == "__main__": main()
