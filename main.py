import yfinance as yf
import os, requests, smtplib, base64, io
import mplfinance as mpf
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# --- 1. CONFIGURATION & DISCOVERY POOL ---
SENDER_EMAIL = "tony55551@gmail.com"

def get_discovery_pool():
    """AI Discovery: The pool of stocks the script 'hunts' to find breakouts for you."""
    return [
        "MAZDOCK.NS", "RVNL.NS", "TEJASNET.NS", "KAYNES.NS", "TITAGARH.NS", 
        "HAL.NS", "BEL.NS", "IRFC.NS", "SJVN.NS", "SUZLON.NS", "GPTINFRA.NS", 
        "DATA-PATTERNS.NS", "NHPC.NS", "WAAREEENER.NS", "RELIANCE.NS"
    ]

# --- 2. CORE UTILITIES: NEWS & CHARTS ---
def get_chart_base64(ticker):
    """Professional Visuals: Candlesticks + Support/Resistance + MAs."""
    try:
        data = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if data.empty: return ""
        
        # Automated Support (Blue) and Resistance (Orange)
        sup, res = data['Low'].min(), data['High'].max()
        
        buf = io.BytesIO()
        mc = mpf.make_marketcolors(up='#27ae60', down='#c0392b', inherit=True)
        s = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
        
        # Plotting Support and Resistance as horizontal lines
        hlines = dict(hlines=[sup, res], colors=['#2980b9', '#e67e22'], linestyle='-.', linewidths=1.5)
        
        mpf.plot(data, type='candle', style=s, hlines=hlines, mav=(50, 200), volume=True, 
                 savefig=dict(fname=buf, format='png', dpi=100))
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')
    except: return ""

def get_relevant_news(ticker, name):
    """Hyper-Relevant News: Boolean search to filter out HR noise."""
    api_key = os.getenv("NEWS_API_KEY")
    core_name = name.split(" ")[0]
    # Query: Anchors company name to financial keywords while excluding hiring noise
    query = f'("{core_name}" OR "{ticker.split(".")[0]}") AND (stock OR "order book" OR results OR breakout) -jobs -hiring'
    url = f"https://newsapi.org/v2/everything?q={query}&sortBy=relevancy&language=en&apiKey={api_key}"
    try:
        art = requests.get(url).json().get('articles', [{}])[0]
        if art.get('title'):
            return f"🔥 <b>{art.get('title')}</b><br><a href='{art.get('url')}'>Source</a>"
        return "Neutral catalyst: Watching price action."
    except: return "Intelligence feed offline."

# --- 3. DATA PROCESSING & TREND PREDICTION ---
def get_stock_intel(ticker, is_discovery=False):
    """Trend Prediction: Golden Cross & Value Logic."""
    try:
        stock = yf.Ticker(ticker)
        inf, hist = stock.info, stock.history(period="1y")
        if hist.empty: return None
        
        price = inf.get('currentPrice', 0)
        
        # 1. Trend Analysis: Golden Cross (50-day crossing above 200-day)
        ma50 = hist['Close'].rolling(50).mean().iloc[-1]
        ma200 = hist['Close'].rolling(200).mean().iloc[-1]
        is_breakout = ma50 > ma200 and price > ma50
        
        # 2. Fundamental Analysis: PE < 20 (Undervalued)
        pe = inf.get('trailingPE')
        is_value = isinstance(pe, (int, float)) and pe < 20

        # AI DISCOVERY FILTER: Only show discovery picks if they are breakouts or value
        if is_discovery and not (is_breakout or is_value):
            return None

        return {
            "name": inf.get('longName', ticker),
            "ticker": ticker,
            "sector": inf.get('sector', 'Other'),
            "price": f"₹{price:.2f}",
            "pe": pe if pe else 'N/A',
            "change": inf.get('regularMarketChangePercent', 0),
            "trend": "🚀 BULLISH (Golden Cross)" if is_breakout else "⚖️ CONSOLIDATING",
            "tag": "AI DISCOVERY" if is_discovery else "WATCHLIST",
            "chart": get_chart_base64(ticker),
            "news": get_relevant_news(ticker, inf.get('longName', ticker))
        }
    except: return None

# --- 4. MAIN PIPELINE ---
def main():
    with open('watchlist.txt', 'r') as f:
        watchlist_tickers = [line.strip() for line in f if line.strip()]
    
    # Process Watchlist + AI Discovery Hunt
    results = [get_stock_intel(t) for t in watchlist_tickers]
    discoveries = [get_stock_intel(t, is_discovery=True) for t in get_discovery_pool() if t not in watchlist_tickers]
    all_data = [r for r in (results + discoveries) if r]

    # SENTIMENT METER: Advance/Decline Ratio
    adv = len([r for r in all_data if r['change'] > 0])
    dec = len([r for r in all_data if r['change'] < 0])
    adr = adv / dec if dec > 0 else adv
    
    sentiment = "NEUTRAL"
    if adr > 2.0: sentiment = "EXTREME GREED"
    elif adr > 1.2: sentiment = "GREED"
    elif adr < 0.5: sentiment = "EXTREME FEAR"
    elif adr < 0.8: sentiment = "FEAR"

    # SECTOR LEADERBOARD logic
    sec_perf = {}
    for r in all_data:
        sec_perf.setdefault(r['sector'], []).append(r['change'])
    
    leaderboard = sorted(
        [{"s": s, "avg": sum(p)/len(p)} for s, p in sec_perf.items()],
        key=lambda x: x['avg'], reverse=True
    )

    # --- 5. HTML ASSEMBLY ---
    html = f"<html><body style='background:#f4f7f6; padding:20px; font-family:sans-serif;'>"
    
    # Sentiment Meter Card
    s_col = {"EXTREME GREED": "#c0392b", "GREED": "#e67e22", "NEUTRAL": "#7f8c8d", "FEAR": "#2980b9", "EXTREME FEAR": "#27ae60"}[sentiment]
    html += f"""<div style="background:{s_col}; color:white; padding:20px; border-radius:12px; text-align:center; margin-bottom:20px;">
        <h2 style="margin:0;">MARKET SENTIMENT: {sentiment}</h2>
        <p style="margin:5px 0 0;">Advance/Decline Ratio: {adr:.2f}</p>
    </div>"""

    # Leaderboard Section
    html += "<div style='background:#2c3e50; color:white; padding:15px; border-radius:12px; margin-bottom:30px;'><h3>📊 Sector Momentum</h3>"
    for e in leaderboard:
        html += f"<p>{e['s']}: <b style='color:{'#27ae60' if e['avg'] > 0 else '#e74c3c'};'>{e['avg']:+.2f}%</b></p>"
    html += "</div>"

    # Sector-Wise Content Cards
    for l_entry in leaderboard:
        sec = l_entry['s']
        html += f"<h2 style='color:#2c3e50; border-bottom:3px solid #3498db; margin-top:40px;'>📂 {sec} Sector</h2>"
        for r in [x for x in all_data if x['sector'] == sec]:
            tag_col = "#9b59b6" if r['tag'] == "AI DISCOVERY" else "#3498db"
            html += f"""
            <div style="background:white; border-radius:15px; padding:20px; margin-bottom:25px; border:1px solid #ddd;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:1.3em; font-weight:bold;">{r['name']} <span style="background:{tag_col}; color:white; font-size:10px; padding:2px 6px; border-radius:4px;">{r['tag']}</span></span>
                    <span style="color:{'#27ae60' if 'BULLISH' in r['trend'] else '#7f8c8d'}; font-weight:bold; font-size:0.9em;">{r['trend']}</span>
                </div>
                <div style="margin:10px 0; font-size:0.95em;">Price: <b>{r['price']}</b> ({r['change']:+.2f}%) | PE: {r['pe']}</div>
                <img src="data:image/png;base64,{r['chart']}" style="width:100%; border-radius:8px; border:1px solid #eee;">
                <div style="background:#f8f9fa; padding:15px; border-radius:10px; margin-top:10px; font-size:0.85em;">{r['news']}</div>
            </div>"""

    html += "</body></html>"
    
    # Send Email
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = SENDER_EMAIL
    msg['Subject'] = f"🚀 Pro AI Intelligence: {datetime.now().strftime('%d %b %Y')}"
    msg.attach(MIMEText(html, 'html'))
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
        srv.login(SENDER_EMAIL, os.getenv("EMAIL_PASS"))
        srv.send_message(msg)

if __name__ == "__main__":
    main()
