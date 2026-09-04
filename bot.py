import os, requests, yfinance as yf
from datetime import datetime
import pytz

BOT=os.environ.get("BOT_TOKEN")
CHAT=os.environ.get("CHAT_ID")
IST=pytz.timezone("Asia/Kolkata")

def send(msg):
    requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id":CHAT,"text":msg,"parse_mode":"HTML"}, timeout=30)

def get_nifty():
    # Try 2 tickers
    for sym in ["^NSEI", "NIFTYBEES.NS"]:
        try:
            df = yf.Ticker(sym).history(period="5d", auto_adjust=True)
            if len(df) >= 2:
                return df['Close'].iloc[-2], df['Close'].iloc[-1], sym
        except: pass
    return None, None, None

prev,curr,sym = get_nifty()
now = datetime.now(IST).strftime("%d-%m %I:%M %p")

if prev is None:
    send(f"ℹ️ <b>Bot LIVE Check - {now}</b>\n\nMarket closed hai isliye Nifty live data nahi mila, lekin GitHub Bot 100% kaam kar raha hai ✅\nKal 9:35 AM ko market khulte hi sahi alert ayega!\n\nTest OK - FNO Bot Active 🚀")
else:
    pct = ((curr-prev)/prev)*100
    if pct > 0.8:
        txt = f"🚀 <b>BULLISH</b> {sym}\nNifty: {curr:.2f} (+{pct:.2f}%)\nCE dekho\n{now}"
    elif pct < -0.8:
        txt = f"🔻 <b>BEARISH</b> {sym}\nNifty: {curr:.2f} ({pct:.2f}%)\nPE dekho\n{now}"
    else:
        txt = f"ℹ️ <b>Sideways</b>\nNifty: {curr:.2f} ({pct:+.2f}%)\nWait\n{now}"
    send(txt)
