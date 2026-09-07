import os, requests, yfinance as yf
from datetime import datetime
import pytz

BOT=os.environ.get("BOT_TOKEN")
CHAT=os.environ.get("CHAT_ID")
IST=pytz.timezone("Asia/Kolkata")

WATCH = ["SOLARINDS.NS","IDEA.NS","RELIANCE.NS","HAL.NS","BEL.NS","BSE.NS","POLYCAB.NS"]

def send(m):
    requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id":CHAT,"text":m,"parse_mode":"HTML"}, timeout=20)

def scan():
    now=datetime.now(IST).strftime("%d-%m %I:%M %p")
    bull=[]; logs=[]
    for sym in WATCH:
        try:
            t=yf.Ticker(sym)
            df=t.history(period="1d", interval="1m") # 1-min LIVE
            if len(df)<5:
                df=t.history(period="2d", interval="5m")
            if df.empty:
                logs.append(f"{sym}: data empty")
                continue
            prev = t.info.get('previousClose') or df['Close'].iloc[0]
            curr = df['Close'].iloc[-1]
            low = df['Low'].min()
            high = df['High'].max()
            pct = ((curr-prev)/prev)*100
            intra = ((high-low)/low)*100
            logs.append(f"{sym.replace('.NS','')}: {curr:.0f} prev {prev:.0f} {pct:+.2f}% intra {intra:.1f}%")
            if pct>=1.0 or intra>=1.8:
                bull.append((sym.replace('.NS',''),curr,pct,intra))
        except Exception as e:
            logs.append(f"{sym} err {e}")

    if bull:
        msg=f"🔥 <b>LIVE {now}</b>\n\n"
        for s,c,p,i in sorted(bull,key=lambda x:x[2],reverse=True):
            msg+=f"• {s} {c:.0f} ({p:+.2f}% / {i:.1f}% intra)\n"
    else:
        msg=f"ℹ️ <b>{now}</b> No 1%+ breakout\n\n" + "\n".join(logs[:10])
    send(msg)

scan()
