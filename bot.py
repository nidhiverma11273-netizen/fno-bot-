import os, requests, yfinance as yf
from datetime import datetime
import pytz

BOT=os.environ.get("BOT_TOKEN")
CHAT=os.environ.get("CHAT_ID")
IST=pytz.timezone("Asia/Kolkata")

# Sirf tumhare main stocks
SYMS = ["SOLARINDS.NS","IDEA.NS","RELIANCE.NS","HAL.NS","BEL.NS","BSE.NS","POLYCAB.NS"]

def send(m):
    requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id":CHAT,"text":m,"parse_mode":"HTML"}, timeout=20)

def scan():
    now=datetime.now(IST).strftime("%d-%m %I:%M %p")
    try:
        # EK HI REQUEST ME SAARE - block nahi hoga
        data = yf.download(SYMS, period="2d", interval="15m", group_by='ticker', threads=False, progress=False)

        bull=[]
        logs=[]
        for sym in SYMS:
            try:
                df = data[sym] if len(SYMS)>1 else data
                if df.empty or len(df)<2:
                    logs.append(f"{sym}: empty")
                    continue
                # Aaj ka data
                df = df.dropna()
                prev_close = df['Close'].iloc[-16] if len(df)>16 else df['Close'].iloc[0] # kal ka close
                curr = df['Close'].iloc[-1]
                low = df['Low'].tail(26).min()
                high = df['High'].tail(26).max()
                pct = ((curr-prev_close)/prev_close)*100
                intra = ((high-low)/low)*100 if low else 0
                logs.append(f"{sym.replace('.NS','')}: {curr:.0f} {pct:+.2f}% intra {intra:.1f}%")
                if pct>=1.0 or intra>=1.8:
                    bull.append((sym.replace('.NS',''),curr,pct,intra))
            except Exception as e:
                logs.append(f"{sym} err")
                continue

        if bull:
            msg=f"🔥 <b>BREAKOUT {now}</b>\n\n"
            for s,c,p,i in sorted(bull,key=lambda x:x[2],reverse=True):
                msg+=f"• {s} {c:.0f} ({p:+.2f}% / {i:.1f}%)\n"
        else:
            msg=f"ℹ️ <b>{now}</b> No 1%+ breakout\n\n" + "\n".join(logs)
        send(msg)
    except Exception as e:
        send(f"⚠️ Error {now}: {str(e)[:100]}")

scan()
