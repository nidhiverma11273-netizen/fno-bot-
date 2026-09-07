import os, requests
from datetime import datetime
import pytz

BOT=os.environ.get("BOT_TOKEN")
CHAT=os.environ.get("CHAT_ID")
IST=pytz.timezone("Asia/Kolkata")

# Direct NSE API use karega - yfinance ka chakkar khatam
def get_nse_price(symbol):
    try:
        # NSE ka live API
        headers={"User-Agent":"Mozilla/5.0"}
        url=f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
        # Pehle session lelo
        s=requests.Session()
        s.get("https://www.nseindia.com", headers=headers, timeout=10)
        r=s.get(url, headers=headers, timeout=10).json()
        price=r['priceInfo']['lastPrice']
        pChange=r['priceInfo']['pChange']
        return price, pChange
    except:
        return None, None

def send(m):
    requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id":CHAT,"text":m,"parse_mode":"HTML"}, timeout=30)

def scan():
    now=datetime.now(IST).strftime("%d-%m %I:%M %p")
    symbols=["SOLARINDS","IDEA","RELIANCE","HAL","BEL","BSE","POLYCAB"]
    bull=[]
    for sym in symbols:
        price, pct = get_nse_price(sym)
        if price and pct and abs(pct)>=1.0:
            bull.append((sym, pct, price))

    if bull:
        msg=f"🔥 <b>LIVE NSE - {now}</b>\n\n"
        for s,p,c in sorted(bull, key=lambda x:x[1], reverse=True):
            msg+=f"• {s} {c:.0f} ({p:+.2f}%)\n"
        # SOLARINDS check
        for s,p,c in bull:
            if s=="SOLARINDS":
                msg+=f"\n✅ SOLARINDS pakda gaya! {c:.0f} ({p:+.2f}%) - Chart wala breakout!"
    else:
        # Debug SOLARINDS ka asli price dikhao
        price, pct = get_nse_price("SOLARINDS")
        msg=f"ℹ️ {now}\nSOLARINDS LIVE: {price} ({pct}%)\nNSE API check kiya."
    send(msg)

scan()
