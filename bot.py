import os, requests, yfinance as yf
from datetime import datetime
import pytz

BOT=os.environ.get("BOT_TOKEN")
CHAT=os.environ.get("CHAT_ID")
IST=pytz.timezone("Asia/Kolkata")

FNO_STOCKS = ["RELIANCE.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","BHARTIARTL.NS","ITC.NS","LT.NS","BAJFINANCE.NS","AXISBANK.NS","MARUTI.NS","SUNPHARMA.NS","TITAN.NS","ONGC.NS","TATAMOTORS.NS","ADANIENT.NS","ADANIPORTS.NS","POWERGRID.NS","NTPC.NS","COALINDIA.NS","HINDALCO.NS","JSWSTEEL.NS","CIPLA.NS","DIVISLAB.NS","EICHERMOT.NS","BAJAJ-AUTO.NS","BRITANNIA.NS","BPCL.NS","INDUSINDBK.NS","TECHM.NS","M&M.NS","UPL.NS","VEDL.NS","INDIGO.NS","ZOMATO.NS","DLF.NS","HAL.NS","BEL.NS","TATAPOWER.NS","PFC.NS","RECLTD.NS","FEDERALBNK.NS","IDFCFIRSTB.NS","PNB.NS","BANKBARODA.NS","MUTHOOTFIN.NS","CHOLAFIN.NS","LICHSGFIN.NS","PERSISTENT.NS","COFORGE.NS","MPHASIS.NS"]

def send(msg):
    requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id":CHAT,"text":msg,"parse_mode":"HTML"}, timeout=60)

def scan():
    now=datetime.now(IST).strftime("%d-%m %I:%M %p")
    bullish=[]
    bearish=[]

    for sym in FNO_STOCKS:
        try:
            t=yf.Ticker(sym)
            # Aaj ka 1-day intraday data
            today=t.history(period="1d", interval="5m")
            prev_close=t.history(period="2d")['Close'].iloc[-2] if len(t.history(period="2d"))>=2 else today['Open'].iloc[0]

            if len(today)==0: continue
            curr=today['Close'].iloc[-1]
            open_p=today['Open'].iloc[0]
            pct_day=((curr-prev_close)/prev_close)*100
            pct_open=((curr-open_p)/open_p)*100 if open_p else 0

            # Subah ke liye 0.7% hi kaafi hai
            if pct_day>=0.7 and pct_open>0.3:
                bullish.append((sym.replace(".NS",""),pct_day,curr))
            elif pct_day<=-0.7 and pct_open<-0.3:
                bearish.append((sym.replace(".NS",""),pct_day,curr))
        except: continue

    bullish=sorted(bullish,key=lambda x:x[1],reverse=True)[:6]
    bearish=sorted(bearish,key=lambda x:x[1])[:6]

    if bullish or bearish:
        msg=f"🔥 <b>F&O LIVE SCAN - {now}</b>\n\n"
        if bullish:
            msg+=f"🚀 <b>TOP BULLISH (+0.7%+):</b>\n"
            for s,p,c in bullish: msg+=f"• {s}: {c:.1f} (+{p:.2f}%)\n"
        if bearish:
            msg+=f"\n🔻 <b>TOP BEARISH (-0.7%+):</b>\n"
            for s,p,c in bearish: msg+=f"• {s}: {c:.1f} ({p:.2f}%)\n"
        msg+=f"\n⚡ 9:35 AM breakout scan"
    else:
        # Sideways pe bhi Nifty ka status bhejo
        try:
            nifty=yf.Ticker("^NSEI").history(period="1d",interval="5m")
            if len(nifty)>0:
                n_close=nifty['Close'].iloc[-1]
                n_open=nifty['Open'].iloc[0]
                n_pct=((n_close-n_open)/n_open)*100
                msg=f"ℹ️ <b>F&O Sideways - {now}</b>\nNifty: {n_close:.1f} ({n_pct:+.2f}% today)\nKoi strong F&O breakout nahi, market flat hai. ✅"
            else:
                msg=f"ℹ️ <b>F&O Sideways - {now}</b>\nAaj 0.7% se bada move nahi hai."
        except:
            msg=f"ℹ️ <b>F&O Sideways - {now}</b>\nNo breakout >0.7%"

    send(msg)

scan()
