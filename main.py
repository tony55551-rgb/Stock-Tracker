import yfinance as yf
import os, requests, smtplib, base64, io
import mplfinance as mpf
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

SENDER_EMAIL = "tony55551@gmail.com"

def get_chart_base64(ticker):
    """Generates a professional candlestick chart with 50/200 MA and Support/Resistance."""
    try:
        data = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if data.empty: return ""
        # Automated Support/Resistance
        sup, res = data['Low'].min(), data['High'].max()
        buf = io.BytesIO()
        mc = mpf.make_marketcolors(up='#27ae60', down='#c0392b', inherit=True)
        s = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
        hlines = dict(hlines=[sup, res], colors=['#2980b9', '#e67e22'], linestyle='-.', linewidths=1.5)
        mpf.plot(data, type='candle', style=s, hlines=hlines, mav=(50, 200), volume=True, 
                 savefig=dict(fname=buf, format='png', dpi=100), title=f"\n{ticker} Analysis")
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')
    except: return ""

def get_sector_intel(ticker):
    try:
        stock = yf.Ticker(ticker)
        inf = stock.info
        hist = stock.history(period="1y")
        price = inf.get('currentPrice', 0)
        ma50 = hist['Close'].rolling(50).mean().iloc[-1]
        ma200 = hist['Close'].rolling(200).mean().iloc[-1]
        
        # NewsAPI Filtering for high-impact financial news
        api_key = os.getenv("NEWS_API_KEY")
        name = inf.get('longName', ticker)
        url = f"https://newsapi.org/v2/everything?q={name.split(' ')[0]} AND (stock OR order OR breakout)&apiKey={api_key}"
        news_data = requests.get(url).json().get('articles', [{}])[0]
        news_text = f"🔥 <b>{news_data.get('title')}</b>" if news_data.get('title') else "Neutral news flow."

        return {
            "name": name, "sector": inf.get('sector', 'Emerging'), "price": price,
            "pe": inf.get('trailingPE', 'N/A'), "eps": inf.get('trailingEps', 'N/A'),
            "change": inf.get('regularMarketChangePercent', 0),
            "trend": "🚀 BULLISH (Golden Cross)" if ma50 > ma200 and price > ma50 else "⚖️ CONSOLIDATING",
            "chart": get_chart_base64(ticker), "news": news_text
        }
    except: return None

def main():
    with open('watchlist.txt', 'r') as f:
        tickers = [line.strip() for line in f if line.strip()]
    
    data_list = [get_sector_intel(t) for t in tickers if get_sector_intel(t)]
    sectors = sorted(list(set(d['sector'] for d in data_list)))

    # TOP SUMMARY: Sector Performance Leaderboard
    summary_html = '<div style="background:#2c3e50; color:white; padding:15px; border-radius:10px; margin-bottom:30px;">'
    summary_html += '<h3>📊 Sector Momentum Leaderboard</h3><table style="width:100%; color:white; font-size:0.9em;">'
    for s in sectors:
        avg_chg = sum(d['change'] for d in data_list if d['sector'] == s) / len([d for d in data_list if d['sector'] == s])
        summary_html += f'<tr><td>{s}</td><td style="text-align:right; color:{"#27ae60" if avg_chg > 0 else "#e74c3c"};">{avg_chg:+.2f}%</td></tr>'
    summary_html += '</table></div>'

    # MAIN BODY: Sector-wise Cards
    body_html = ""
    for s in sectors:
        body_html += f'<h2 style="color:#2c3e50; border-bottom:2px solid #3498db; padding-bottom:5px;">📂 {s} Sector</h2>'
        for d in [x for x in data_list if x['sector'] == s]:
            is_val = isinstance(d['pe'], (int, float)) and d['pe'] < 20
            style = "border:2px solid #27ae60; box-shadow:0 4px 10px rgba(39,174,96,0.2);" if is_val else "border:1px solid #ddd;"
            body_html += f"""
            <div style="background:white; border-radius:12px; padding:20px; margin-bottom:20px; {style}">
                <div style="display:flex; justify-content:space-between; font-weight:bold;">
                    <span>{d['name']} {"<span style='background:#27ae60; color:white; font-size:10px; padding:2px 5px; border-radius:4px;'>VALUE</span>" if is_val else ""}</span>
                    <span style="color:{'#27ae60' if 'BULLISH' in d['trend'] else '#7f8c8d'};">{d['trend']}</span>
                </div>
                <div style="margin:10px 0; font-size:0.9em; color:#444;">Price: <b>₹{d['price']:.2f}</b> ({d['change']:+.2f}%) | PE: {d['pe']} | EPS: {d['eps']}</div>
                <img src="data:image/png;base64,{d['chart']}" style="width:100%; border-radius:8px;">
                <div style="background:#f8f9fa; padding:10px; border-radius:8px; margin-top:10px; font-size:0.85em;">{d['news']}</div>
            </div>"""

    full_html = f"<html><body style='background:#f4f7f6; padding:20px; font-family:sans-serif;'>{summary_html}{body_html}</body></html>"
    msg = MIMEMultipart(); msg['From'] = SENDER_EMAIL; msg['To'] = SENDER_EMAIL
    msg['Subject'] = f"🚀 Institutional Intel: {datetime.now().strftime('%d %b %Y')}"
    msg.attach(MIMEText(full_html, 'html'))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
        srv.login(SENDER_EMAIL, os.getenv("EMAIL_PASS")); srv.send_message(srv.send_message(msg))

if __name__ == "__main__": main()
