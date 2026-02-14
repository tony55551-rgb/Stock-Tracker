import yfinance as yf
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 1. CONFIGURATION
# Your current holdings (from your portfolio)
MY_STOCKS = ["TATAPOWER.NS", "JIOFIN.NS", "CGPOWER.NS", "KAYNES.NS", "SUZLON.NS"]
SENDER_EMAIL = "tony55551@gmail.com" # <--- REPLACE WITH YOUR GMAIL ADDRESS

def get_market_report():
    report = "📈 DAILY MARKET REPORT\n" + "="*30 + "\n\n"
    for ticker in MY_STOCKS:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1d")
        if not df.empty:
            price = df['Close'].iloc[-1]
            open_p = df['Open'].iloc[-1]
            change = ((price - open_p) / open_p) * 100
            
            # --- SAFER NEWS FETCHING ---
            news = stock.news
            headline = "No recent news."
            if news and len(news) > 0:
                # Use .get() to avoid the 'KeyError' crash
                headline = news[0].get('title', news[0].get('summary', "Headline unavailable"))
            
            report += f"{ticker:12} | ₹{price:8.2f} ({change:+.2f}%)\n"
            report += f"   Latest: {headline}\n"
            report += "-"*35 + "\n"
    return report

def send_email(content):
    sender_email = "tony55551@gmail.com"
    # This pulls the 16-digit key from your GitHub Secrets
    app_password = os.getenv("EMAIL_PASS")
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = sender_email
    msg['Subject'] = "🚀 Your Automated Market Update"
    msg.attach(MIMEText(content, 'plain'))
    
    try:
        # Switching to SMTP_SSL on Port 465 for better server compatibility
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)
        print("Success: Email sent!")
    except Exception as e:
        print(f"Detailed Error: {e}")

if __name__ == "__main__":
    report_data = get_market_report()
    send_email(report_data)
