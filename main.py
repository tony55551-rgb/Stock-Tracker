import yfinance as yf
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SENDER_EMAIL = "tony55551@gmail.com"

def get_ai_intel(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Fundamental Data
        pe = info.get('trailingPE', 'N/A')
        eps = info.get('trailingEps', 'N/A')
        m_cap = info.get('marketCap', 0)
        price = info.get('currentPrice', 'N/A')
        change = info.get('regularMarketChangePercent', 0)

        # Growth Category Logic
        cap_type = "MID-CAP" if m_cap > 200000000000 else "SMALL-CAP"
        cap_color = "#2980b9" if cap_type == "MID-CAP" else "#d35400"

        # AI Sector/Institutional Scan
        news = stock.news
        intel_alert = "Neutral: Watching for catalysts."
        keywords = ["order book", "l1 bidder", "goldman", "jp morgan", "contract", "breakout"]
        
        for n in news:
            title = n.get('title', "").lower()
            if any(k in title for k in keywords):
                intel_alert = f"🎯 <b>{n.get('title')}</b>"
                break

        return f"""
        <div style="background: white; border-radius: 10px; padding: 20px; margin-bottom: 15px; border-left: 6px solid {cap_color}; font-family: 'Segoe UI', Arial, sans-serif; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between;">
                <span style="font-size: 1.3em; font-weight: bold; color: #2c3e50;">{ticker}</span>
                <span style="background: {cap_color}; color: white; padding: 2px 12px; border-radius: 15px; font-size: 0.8em; height: 20px;">{cap_type}</span>
            </div>
            <div style="margin: 15px 0; display: flex; justify-content: space-between; font-size: 0.95em;">
                <span>Price: <b>₹{price}</b> (<span style="color: {'#27ae60' if change >= 0 else '#c0392b'};">{change:+.2f}%</span>)</span>
                <span>PE: <b>{pe if pe == 'N/A' else f"{pe:.2f}"}</b></span>
                <span>EPS: <b>{eps if eps == 'N/A' else f"{eps:.2f}"}</b></span>
            </div>
            <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; font-size: 0.9em; line-height: 1.4;">
                <span style="color: #7f8c8d; font-weight: bold; text-transform: uppercase; font-size: 0.75em;">AI Intel & Order Flow:</span><br>
                {intel_alert}
            </div>
        </div>
        """
    except Exception: return ""

def main():
    with open('watchlist.txt', 'r') as f:
        stocks = [line.strip() for line in f if line.strip()]

    html_report = f"""
    <html>
    <body style="background-color: #f0f2f5; padding: 30px; margin: 0;">
        <div style="max-width: 600px; margin: auto;">
            <h1 style="color: #1a2a3a; text-align: center; margin-bottom: 5px;">Market Intelligence</h1>
            <p style="text-align: center; color: #7f8c8d; margin-bottom: 30px;">Emerging Small/Mid-Cap Growth Scan</p>
    """
    
    for ticker in stocks:
        html_report += get_ai_intel(ticker)

    html_report += """
            <p style="text-align: center; font-size: 0.7em; color: #bdc3c7; margin-top: 30px;">
                Securely generated via Tony's AI Hub. Data: Yahoo Finance.
            </p>
        </div>
    </body>
    </html>
    """
    send_email(html_report)

def send_email(html_content):
    app_password = os.getenv("EMAIL_PASS")
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = SENDER_EMAIL
    msg['Subject'] = "🔥 Daily AI Growth Intel: " + str(len(html_content))[:2] + " Stocks Scanned"
    msg.attach(MIMEText(html_content, 'html'))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, app_password)
        server.send_message(msg)

if __name__ == "__main__":
    main()
