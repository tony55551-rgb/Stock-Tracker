import yfinance as yf
import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

SENDER_EMAIL = "tony55551@gmail.com"

def get_refined_news(ticker, company_name):
    api_key = os.getenv("NEWS_API_KEY")
    from_date = (datetime.now() - timedelta(days=4)).strftime('%Y-%m-%d')
    core_name = company_name.split(' ')[0]
    clean_ticker = ticker.split('.')[0]
    
    # AI BOOLEAN QUERY: Targets financial catalysts & institutional movement
    query = f'("{core_name}" OR "{clean_ticker}") AND (stock OR "order book" OR "L1 bidder" OR results OR breakout OR multibagger)'
    url = f"https://newsapi.org/v2/everything?q={query}&from={from_date}&language=en&sortBy=relevancy&apiKey={api_key}"
    
    try:
        response = requests.get(url).json()
        for art in response.get('articles', []):
            if clean_ticker.lower() in art['title'].lower() or core_name.lower() in art['title'].lower():
                return f"🔥 <b>{art['title']}</b><br><a href='{art['url']}'>View Source</a>"
        return "Neutral: Watching for financial catalysts."
    except Exception: return "News Service Unavailable"

def get_stock_intelligence(ticker):
    try:
        stock = yf.Ticker(ticker)
        # Fetch 1 year of data for MA crossover analysis
        hist = stock.history(period="1y")
        if hist.empty: return ""
        
        info = stock.info
        name = info.get('longName', ticker)
        price = info.get('currentPrice', 0)
        pe = info.get('trailingPE', 'N/A')
        eps = info.get('trailingEps', 'N/A')
        change = info.get('regularMarketChangePercent', 0)

        # 1. TREND PREDICTOR: Golden Cross Logic
        ma50 = hist['Close'].rolling(window=50).mean().iloc[-1]
        ma200 = hist['Close'].rolling(window=200).mean().iloc[-1]
        is_breakout = ma50 > ma200 and price > ma50
        trend_label = "🚀 BREAKOUT (Golden Cross)" if is_breakout else "⚖️ CONSOLIDATING"
        trend_color = "#27ae60" if is_breakout else "#7f8c8d"

        # 2. VALUE SCAN: PE < 20 Highlight
        is_value = isinstance(pe, (int, float)) and pe < 20
        card_style = "border: 2px solid #27ae60; box-shadow: 0 4px 12px rgba(39,174,96,0.2);" if is_value else "border-left: 8px solid #3498db;"
        value_badge = '<span style="background: #27ae60; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.7em;">VALUE PICK</span>' if is_value else ''

        news_intel = get_refined_news(ticker, name)

        return f"""
        <div style="background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; {card_style} font-family: sans-serif;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 1.25em; font-weight: bold; color: #1a2a3a;">{name} {value_badge}</span>
                <span style="color: {trend_color}; font-weight: bold; font-size: 0.85em;">{trend_label}</span>
            </div>
            <div style="margin: 15px 0; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; text-align: center;">
                <div style="background: #f8f9fa; padding: 10px; border-radius: 8px;">Price: <b>₹{price:.2f}</b><br><span style="color: {'#27ae60' if change >= 0 else '#c0392b'}; font-weight: bold;">{change:+.2f}%</span></div>
                <div style="background: #f8f9fa; padding: 10px; border-radius: 8px;">PE: <b>{pe if pe == 'N/A' else f"{pe:.2f}"}</b></div>
                <div style="background: #f8f9fa; padding: 10px; border-radius: 8px;">EPS: <b>{eps if eps == 'N/A' else f"{eps:.2f}"}</b></div>
            </div>
            <div style="background: #eef2f3; padding: 15px; border-radius: 8px; border-top: 1px solid #ddd;">
                <span style="font-size: 0.7em; font-weight: bold; color: #7f8c8d; text-transform: uppercase;">AI Intel & Order Visibility:</span><br>
                <div style="margin-top: 5px; font-size: 0.9em; line-height: 1.4;">{news_intel}</div>
            </div>
        </div>
        """
    except Exception: return ""

def main():
    with open('watchlist.txt', 'r') as f:
        stocks = [line.strip() for line in f if line.strip()]
    
    html_report = f"""<html><body style="background-color: #f4f7f6; padding: 20px; font-family: sans-serif;">
        <h1 style="text-align: center; color: #1a2a3a; margin-bottom: 5px;">Multibagger Intel Dashboard</h1>
        <p style="text-align: center; color: #7f8c8d; margin-bottom: 30px;">Refined Scan: Order Books | Value | Trend Crossovers</p>"""
    
    for ticker in stocks:
        html_report += get_stock_intelligence(ticker)
        
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

if __name__ == "__main__":
    main()
