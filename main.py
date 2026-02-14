import yfinance as yf
import os, requests, smtplib, base64, io
import mplfinance as mpf
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

SENDER_EMAIL = "tony55551@gmail.com"

def get_chart_base64(ticker):
    """Generates a professional chart and returns it as a Base64 string for HTML embedding."""
    try:
        data = yf.download(ticker, period="6mo", interval="1d")
        if data.empty: return ""
        
        # Automated Support/Resistance (6-Month Pivot)
        sup = data['Low'].min()
        res = data['High'].max()
        
        # Save to buffer
        buf = io.BytesIO()
        mc = mpf.make_marketcolors(up='#27ae60', down='#c0392b', inherit=True)
        s = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
        
        # Plotting Support (Blue) and Resistance (Orange)
        hlines = dict(hlines=[sup, res], colors=['#2980b9', '#e67e22'], linestyle='-.', linewidths=1.5)
        
        mpf.plot(data, type='candle', style=s, hlines=hlines, mav=(50, 200),
                 volume=True, savefig=dict(fname=buf, format='png', dpi=100))
        
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')
    except: return ""

def get_news(ticker, name):
    api_key = os.getenv("NEWS_API_KEY")
    query = f'("{name.split(" ")[0]}" OR "{ticker.split(".")[0]}") AND (stock OR "order book" OR contract)'
    url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=relevancy&apiKey={api_key}"
    try:
        art = requests.get(url).json().get('articles', [{}])[0]
        return f"🔥 <b>{art.get('title', 'No news found')}</b>" if art.get('title') else "Neutral catalyst."
    except: return "News Service Unavailable"

def get_stock_card(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        name = info.get('longName', ticker)
        price, pe, eps = info.get('currentPrice', 0), info.get('trailingPE', 'N/A'), info.get('trailingEps', 'N/A')
        
        chart_b64 = get_chart_base64(ticker)
        news = get_news(ticker, name)
        
        # Logical Indicators
        is_value = isinstance(pe, (int, float)) and pe < 20
        value_tag = '<span style="background:#27ae60;color:white;padding:2px 6px;border-radius:4px;font-size:10px;">VALUE</span>' if is_value else ""
        
        return f"""
        <div style="background:white; border-radius:15px; padding:20px; margin-bottom:25px; border:1px solid #ddd; font-family:sans-serif;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:1.4em; font-weight:bold;">{name} {value_tag}</span>
                <span style="color:#7f8c8d; font-size:0.9em;">{ticker}</span>
            </div>
            <div style="margin:15px 0; display:grid; grid-template-columns:1fr 1fr; gap:10px; font-size:0.9em;">
                <div>Price: <b>₹{price:.2f}</b> | PE: <b>{pe}</b></div>
                <div style="text-align:right; color:#2980b9;">Support: <b>{info.get('fiftyDayAverage', 0):.1f}</b></div>
            </div>
            <img src="data:image/png;base64,{chart_b64}" style="width:100%; border-radius:8px; margin:10px 0;">
            <div style="background:#f8f9fa; padding:12px; border-radius:8px; font-size:0.85em;">
                <b>AI ANALYST:</b> {news}
            </div>
        </div>
        """
    except: return ""

def main():
    with open('watchlist.txt', 'r') as f:
        stocks = [line.strip() for line in f if line.strip()]
    
    html = f"""<html><body style="background:#f0f2f5; padding:20px;">
        <h1 style="text-align:center; color:#1a2a3a;">Professional Intelligence Report</h1>"""
    for s in stocks: html += get_stock_card(s)
    html += "</body></html>"
    
    msg = MIMEMultipart(); msg['From'] = SENDER_EMAIL; msg['To'] = SENDER_EMAIL
    msg['Subject'] = f"📈 Visual Market Intel: {datetime.now().strftime('%d %b %Y')}"
    msg.attach(MIMEText(html, 'html'))
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
        srv.login(SENDER_EMAIL, os.getenv("EMAIL_PASS"))
        srv.send_message(msg)

if __name__ == "__main__": main()
