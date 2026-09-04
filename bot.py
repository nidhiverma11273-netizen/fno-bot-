import os, yfinance as yf, requests
from datetime import datetime
import pytz

BOT=os.environ.get("BOT_TOKEN")
CHAT=os.environ.get("CHAT_ID")
IST=pytz.timezone("Asia/Kolkata")

def send(msg):
    requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id":CHAT,"text":msg,"parse_mode":"HTML"}, timeout=30)

def check():
    now=datetime.now(IST)
    # NSE data
    try:
        nifty=yf.Ticker("^NSEI").history(period="2d")
        if len(nifty)<2: return send(f"⚠️ Data nahi mila {now.strftime('%d-%m %H:%M')}")
        prev=nifty['Close'].iloc[-2]
        curr=nifty['Close'].iloc[-1]
        pct=((curr-prev)/prev)*100
        
        # Logic
        if pct>1.0:
            send(f"🚀 <b>BULLISH ALERT!</b>\nNifty: {curr:.2f} (+{pct:.2f}%)\nCE Buy karo! Market tez!\n{now.strftime('%d-%m %H:%M')}")
        elif pct<-1.0:
            send(f"🔻 <b>BEARISH ALERT!</b>\nNifty: {curr:.2f} ({pct:.2f}%)\nPE Buy karo! Market gira!\n{now.strftime('%d-%m %H:%M')}")
        else:
            send(f"ℹ️ <b>Sideways</b>\nNifty: {curr:.2f} ({pct:+.2f}%)\nNo clear trade. Wait.\n{now.strftime('%d-%m %H:%M')}")
    except Exception as e:
        send(f"❌ Error: {e}")

check()
