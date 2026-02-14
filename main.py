import yfinance as yf
import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

SENDER_EMAIL = "tony55551@gmail.com"

def get_reliable_news(ticker, company_name):
    api_key = os.getenv("NEWS_API_KEY")
    from_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
    core_name = company_name.split(' ')[0]
    # Boolean query to filter for investment-related news
    query = f'("{core_name}" OR "{ticker}") AND (stock OR shares OR "order book" OR results OR breakout OR multibagger)'
    url = f"https://newsapi.org/v2/everything?q={query}&from={from_date}&language=en&sortBy=relevancy&apiKey={api_key}"
    try:
        response = requests.get(url).json()
        for art in response.get('articles', []):
            title = art['title'].lower()
            if ticker.split('.')[0].lower() in title or core_name.lower() in title:
                return f"🔥 <b>{art['title']}</b><br><a href='{art['url']}'>View Source</a>"
        return "Neutral: Watching for financial catalysts."
    except Exception: return "News Error"

def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        name = info.get('longName', ticker.split('.')[0])
        price = info.get('currentPrice', 'N/A')
        pe = info.get('trailingPE', 'N/A')
        eps = info.get('trailingEps', 'N/A')
        m_cap = info.get('marketCap', 0)
        change = info.get('regularMarketChangePercent', 0)
        cap_type = "MID-CAP" if m_cap > 200000000000 else "SMALL-CAP"
        cap_color = "#2980b9" if cap_type == "MID-CAP" else "#d35400"
        
        news_intel = get_reliable_news(ticker, name)
        
        return f"""
        <div style="background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; border-left: 8px solid {cap_color}; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 1.4em; font-weight: bold; color: #1a2a3a;">{name} ({ticker})</span>
                <span style="background: {cap_color}; color: white; padding: 3px 12px; border-radius: 20px; font-size: 0.8em; font-weight: bold;">{cap_type}</span>
            </div>
            <div style="margin: 15px 0; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; font-size: 0.9em;">
                <div style="background: #f8f9fa; padding: 10px; border-radius: 8px; text-align: center;">Price: <b>₹{price}</b><br><span style="color: {'#27ae60' if change >= 0 else '#c0392b'};">{change:+.2f}%</span></div>
                <div style="background: #f8f9fa; padding: 10px; border-radius: 8px; text-align: center;">PE: <b>{pe if pe == 'N/A' else f"{pe:.2f}"}</b></div>
                <div style="background: #f8f9fa; padding: 10px; border-radius: 8px; text-align: center;">EPS: <b>{eps if eps == 'N/A' else f"{eps:.2f}"}</b></div>
            </div>
            <div style="background: {'#fff4e5' if '🔥' in news_intel else '#eef2f3'}; padding: 15px; border-radius: 8px; border-top: 1px solid #eee;">
                <span style="font-size: 0.75em; font-weight: bold; color: #7f8c8d;">AI INTEL & ORDER VISIBILITY:</span><br>
                <div style="margin-top: 5px; font-size: 0.95em;">{news_intel}</div>
            </div>
        </div>
        """
    except Exception: return ""

def main():
    with open('watchlist.txt', 'r') as f:
        stocks = [line.strip() for line in f if line.strip()]
    html_report = f"""<html><body style="background-color: #f0f2f5; padding: 20px; font-family: sans-serif;">
        <h1 style="text-align: center; color: #1a2a3a;">Multibagger Scan</h1>"""
    for ticker in stocks: html_report += get_stock_data(ticker)
    html_report += "</body></html>"
    send_email(html_report)

def send_email(html_body):
    app_password = os.getenv("EMAIL_PASS")
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = SENDER_EMAIL
    msg['Subject'] = f"🚀 AI Market Scan: {datetime.now().strftime('%d %b %Y')}"
    msg.attach(MIMEText(html_body, 'html'))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, app_password)
        server.send_message(msg)

if __name__ == "__main__": main()
