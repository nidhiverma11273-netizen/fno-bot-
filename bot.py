import os, requests, yfinance as yf
from datetime import datetime
import pytz

BOT=os.environ.get("BOT_TOKEN")
CHAT=os.environ.get("CHAT_ID")
IST=pytz.timezone("Asia/Kolkata")

# F&O + Tumhare Special Stocks
FNO = ["SOLARINDS.NS","RELIANCE.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","BHARTIARTL.NS","ITC.NS","LT.NS","BAJFINANCE.NS","AXISBANK.NS","MARUTI.NS","SUNPHARMA.NS","TITAN.NS","ONGC.NS","TATAMOTORS.NS","ADANIENT.NS","ADANIPORTS.NS","POWERGRID.NS","NTPC.NS","HAL.NS","BEL.NS","TATAPOWER.NS","PFC.NS","IDEA.NS","PAYTM.NS","POLYCAB.NS","RVNL.NS","IRFC.NS","BSE.NS","MCX.NS"]

def send(m):
    requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id":CHAT,"text":m,"parse_mode":"HTML"}, timeout=30)

def scan():
    now=datetime.now(IST).strftime("%d-%m %I:%M %p")
    bull=[]
    for sym in FNO:
        try:
            t=yf.Ticker(sym)
            df=t.history(period="1d", interval="5m")
            if len(df)<2:
                df=t.history(period="2d")
            prev=df['Open'].iloc[0] if len(df)>0 else df['Close'].iloc[-2]
            curr=df['Close'].iloc[-1]
            pct=((curr-prev)/prev)*100
            vol=df['Volume'].iloc[-1]
            avg_vol=df['Volume'].mean()
            vol_ratio=vol/avg_vol if avg_vol>0 else 0
            if pct>=1.0 and vol_ratio>1.2: # 1% + volume tez
                bull.append((sym.replace(".NS",""),pct,curr,vol_ratio))
        except: continue

    bull=sorted(bull,key=lambda x:x[1],reverse=True)[:10]
    if bull:
        msg=f"🔥 <b>BREAKOUT SCAN - {now}</b>\n\n"
        for s,p,c,vr in bull:
            star=" ⭐⭐" if s=="SOLARINDS" else ""
            msg+=f"• {s} {c:.0f} (+{p:.2f}%) Vol {vr:.1f}x{star}\n"
        msg+=f"\nSOLARINDS chart jaisa breakout!"
    else:
        msg=f"ℹ️ <b>{now}</b>\nAbhi 1%+ Volume breakout nahi."
    send(msg)

scan()
