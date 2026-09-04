import os, yfinance as yf, requests
from datetime import datetime
import pytz

BOT = os.environ.get("BOT_TOKEN")
CHAT = os.environ.get("CHAT_ID")
IST = pytz.timezone("Asia/Kolkata")

def send(msg):
    url = f"https://api.telegram.org/bot{BOT}/sendMessage"
    requests.post(url, data={"chat_id": CHAT, "text": msg, "parse_mode": "HTML"}, timeout=30)

try:
    nifty = yf.Ticker("^NSEI").history(period="5d")
    if len(nifty) < 2:
        send("⚠️ Nifty data nahi mila")
    else:
        prev = nifty['Close'].iloc[-2]
        curr = nifty['Close'].iloc[-1]
        pct = ((curr-prev)/prev)*100
        now = datetime.now(IST).strftime("%d-%m %I:%M %p")

        if pct > 1.0:
            txt = f"🚀 <b>BULLISH BREAKOUT!</b>\n\nNifty: {curr:.2f} <b>(+{pct:.2f}%)</b>\nTrend: Strong Up\nAction: <b>CE Buy karo</b>\nTime: {now}"
        elif pct < -1.0:
            txt = f"🔻 <b>BEARISH BREAKDOWN!</b>\n\nNifty: {curr:.2f} <b>({pct:.2f}%)</b>\nTrend: Strong Down\nAction: <b>PE Buy karo</b>\nTime: {now}"
        else:
            txt = f"ℹ️ <b>Sideways Market</b>\n\nNifty: {curr:.2f} ({pct:+.2f}%)\nNo big move. Wait for breakout.\nTime: {now}"
        send(txt)
        print("Sent", pct)
except Exception as e:
    send(f"❌ Bot Error: {e}")
