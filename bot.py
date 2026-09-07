import os, requests, yfinance as yf
from datetime import datetime
import pytz

BOT=os.environ.get("BOT_TOKEN")
CHAT=os.environ.get("CHAT_ID")
IST=pytz.timezone("Asia/Kolkata")

FNO = ["SOLARINDS.NS","IDEA.NS","RELIANCE.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","BHARTIARTL.NS","ITC.NS","LT.NS","BAJFINANCE.NS","AXISBANK.NS","MARUTI.NS","HAL.NS","BEL.NS","TATAPOWER.NS","BSE.NS","PAYTM.NS","POLYCAB.NS"]

def send(m):
    requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id":CHAT,"text":m,"parse_mode":"HTML"}, timeout=30)

def scan():
    now=datetime.now(IST).strftime("%d-%m %I:%M %p")
    bull=[]
    debug=""
    for sym in FNO:
        try:
            t=yf.Ticker(sym)
            df=t.history(period="2d", interval="5m")
            if len(df)<2: continue
            prev_close=df['Close'].iloc[-2] if len(df)>50 else t.info.get('previousClose', df['Close'].iloc[0])
            # Aaj ka data
            today=df.tail(70)
            curr=today['Close'].iloc[-1]
            day_low=today['Low'].min()
            day_high=today['High'].max()
            # 2 tarah se % - Prev Close se aur Low se High tak
            pct_close=((curr-prev_close)/prev_close)*100 if prev_close else 0
            pct_intra=((day_high-day_low)/day_low)*100 if day_low else 0

            if sym=="SOLARINDS.NS":
                debug=f"SOLAR DEBUG: Prev {prev_close:.0f} Curr {curr:.0f} Low {day_low:.0f} High {day_high:.0f} => {pct_close:.2f}% / Intra {pct_intra:.2f}%"

            if pct_close>=1.5 or pct_intra>=2.5: # SOLARINDS jaisa move pakad lega
                bull.append((sym.replace(".NS",""),pct_close,curr,pct_intra))
        except Exception as e:
            continue

    bull=sorted(bull,key=lambda x:x[1],reverse=True)[:10]
    if bull:
        msg=f"🔥 <b>BREAKOUT - {now}</b>\n\n"
        for s,p,c,intra in bull:
            msg+=f"• {s} {c:.0f} (+{p:.2f}% / Intra {intra:.1f}%)\n"
        if debug: msg+=f"\n{debug}"
    else:
        msg=f"ℹ️ <b>{now}</b>\n1.5%+ Close ya 2.5%+ Intra breakout nahi.\n{debug}"
    send(msg)

scan()
