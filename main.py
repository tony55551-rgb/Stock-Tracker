import yfinance as yf
import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

SENDER_EMAIL = "tony55551@gmail.com"

def get_reliable_news(company_name):
    """Fetches high-quality news using NewsAPI keywords."""
    api_key = os.getenv("NEWS_API_KEY")
    # Search for news from the last 3 days
    from_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
    url = f"https://newsapi.org/v2/everything?q={company_name}&from={from_date}&language=en&sortBy=relevancy&apiKey={api_key}"
    
    try:
        response = requests.get(url).json()
        articles = response.get('articles', [])
        
        # Multibagger Keyword Filter
        intel_keywords = ["order book", "l1 bidder", "contract", "goldman", "jp morgan", "multibagger", "breakout"]
        for art in articles[:10]: # Check top 10 relevant news
            title = art['title'].lower()
            if any(k in title for k in intel_keywords):
                return f"🔥 <b>CRITICAL: {art['title']}</b><br><a href='{art['url']}'>Read Article</a>"
        
        # Fallback to the latest general news if no 'intel' keywords hit
        if articles:
            return f"🗞️ {articles[0]['title']}<br><a href='{articles[0]['url']}'>View Source</a>"
        return "Neutral: No major news in last 3 days."
    except Exception:
        return "News API connection failed."

def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        name = info.get('longName', ticker.split('.')[0])
        
        # Data Extraction
        price = info.get('currentPrice', 'N/A')
        pe = info.get('trailingPE', 'N/A')
        eps = info.get('trailingEps', 'N/A')
        fv = info.get('faceValue', 'N/A')
        m_cap = info.get('marketCap', 0)
        change = info.get('regularMarketChangePercent', 0)
        
        cap_type = "MID-CAP" if m_cap > 200000000000 else "SMALL-CAP"
        cap_color = "#2980b9" if cap_type == "MID-CAP" else "#d35400"
        
        news_intel = get_reliable_news(name)
        
        return f"""
        <div style="background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; border-left: 8px solid {cap_color}; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 1.4em; font-weight: bold; color: #1a2a3a;">{name} ({ticker})</span>
                <span style="background: {cap_color}; color: white; padding: 3px 12px; border-radius: 20px; font-size: 0.8em; font-weight: bold;">{cap_type}</span>
            </div>
            <div style="margin: 15px 0; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; font-size: 0.9em; color: #444;">
                <div style="background: #f8f9fa; padding: 10px; border-radius: 8px; text-align: center;">
                    Price<br><b style="font-size: 1.2em;">₹{price}</b><br>
                    <span style="color: {'#27ae60' if change >= 0 else '#c0392b'}; font-weight: bold;">{change:+.2f}%</span>
                </div>
                <div style="background: #f8f9fa; padding: 10px; border-radius: 8px; text-align: center;">
                    PE Ratio<br><b style="font-size: 1.2em;">{pe if pe == 'N/A' else f"{pe:.2f}"}</b><br>
                    <span style="color: #7f8c8d;">EPS: {eps if eps == 'N/A' else f"{eps:.2f}"}</span>
                </div>
                <div style="background: #f8f9fa; padding: 10px; border-radius: 8px; text-align: center;">
                    Face Value<br><b style="font-size: 1.2em;">{fv}</b><br>
                    <span style="color: #7f8c8d;">Multibagger Scan</span>
                </div>
            </div>
            <div style="background: {'#fff4e5' if '🔥' in news_intel else '#eef2f3'}; padding: 15px; border-radius: 8px; border-top: 1px solid #eee;">
                <span style="font-size: 0.75em; font-weight: bold; color: #7f8c8d; text-transform: uppercase;">AI Intel & Order Visibility:</span><br>
                <div style="margin-top: 5px; font-size: 0.95em; color: #333;">{news_intel}</div>
            </div>
        </div>
        """
    except Exception: return ""

def main():
    with open('watchlist.txt', 'r') as f:
        stocks = [line.strip() for line in f if line.strip()]

    html_report = """
    <html>
    <body style="background-color: #f0f2f5; padding: 20px; font-family: 'Helvetica Neue', Arial, sans-serif;">
        <div style="max-width: 650px; margin: auto;">
            <div style="text-align: center; margin-bottom: 40px;">
                <h1 style="color: #1a2a3a; margin-bottom: 5px;">Multibagger Intelligence</h1>
                <p style="color: #7f8c8d; font-size: 1.1em;">Daily Analysis: High Order Books & Institutional Intel</p>
                <div style="height: 4px; width: 60px; background: #3498db; margin: 15px auto;"></div>
            </div>
    """
    
    for ticker in stocks:
        html_report += get_stock_data(ticker)

    html_report += f"""
            <p style="text-align: center; font-size: 0.8em; color: #bdc3c7; margin-top: 40px;">
                Report Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}<br>
                Powered by NewsAPI & Tony's AI Hub
            </p>
        </div>
    </body>
    </html>
    """
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
