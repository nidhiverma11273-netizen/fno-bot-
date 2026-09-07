import os, requests, yfinance as yf, time
from datetime import datetime
import pytz

BOT=os.environ.get("BOT_TOKEN")
CHAT=os.environ.get("CHAT_ID")
IST=pytz.timezone("Asia/Kolkata")

FNO = ["RELIANCE.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","BHARTIARTL.NS","ITC.NS","LT.NS","BAJFINANCE.NS","AXISBANK.NS","MARUTI.NS","SUNPHARMA.NS","TITAN.NS","ONGC.NS","TATAMOTORS.NS","ADANIENT.NS","ADANIPORTS.NS","POWERGRID.NS","NTPC.NS","COALINDIA.NS","HINDALCO.NS","JSWSTEEL.NS","CIPLA.NS","DIVISLAB.NS","EICHERMOT.NS","BAJAJ-AUTO.NS","BPCL.NS","INDUSINDBK.NS","TECHM.NS","M&M.NS","VEDL.NS","INDIGO.NS","ZOMATO.NS","DLF.NS","HAL.NS","BEL.NS","TATAPOWER.NS","PFC.NS","FEDERALBNK.NS","PNB.NS","BANKBARODA.NS"]

def send(m):
    requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id":CHAT,"text":m,"parse_mode":"HTML"}, timeout=30)

def scan():
    now=datetime.now(IST).strftime("%d-%m %I:%M %p")
    bull=[]; bear=[]
    for sym in FNO:
        try:
            t=yf.Ticker(sym)
            # 1m data lo - 9:35 pe bhi mil jayega
            df=t.history(period="1d", interval="1m")
            if len(df)<5:
                df=t.history(period="2d")
                if len(df)<2: continue
                prev=df['Close'].iloc[-2]; curr=df['Close'].iloc[-1]
            else:
                prev=df['Open'].iloc[0]; curr=df['Close'].iloc[-1]
            pct=((curr-prev)/prev)*100
            if pct>=0.6: bull.append((sym.replace(".NS",""),pct,curr))
            elif pct<=-0.6: bear.append((sym.replace(".NS",""),pct,curr))
        except: continue

    bull=sorted(bull,key=lambda x:x[1],reverse=True)[:5]
    bear=sorted(bear,key=lambda x:x[1])[:5]

    if bull or bear:
        msg=f"🔥 <b>F&O OPEN SCAN - {now}</b>\nMarket OPEN Hai!\n\n"
        if bull:
            msg+="🚀 <b>BULLISH:</b>\n"
            for s,p,c in bull: msg+=f"• {s} {c:.1f} (+{p:.2f}%)\n"
        if bear:
            msg+="\n🔻 <b>BEARISH:</b>\n"
            for s,p,c in bear: msg+=f"• {s} {c:.1f} ({p:.2f}%)\n"
    else:
        # Agar koi 0.6% nahi toh top movers dikhao
        msg=f"ℹ️ <b>Market Open - {now}</b>\nAbhi tak 0.6%+ breakout nahi, 10 min wait karo!\nBot LIVE hai ✅"
    send(msg)

scan()
