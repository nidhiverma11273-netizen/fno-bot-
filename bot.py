import os, requests, yfinance as yf
from datetime import datetime
import pytz

BOT=os.environ.get("BOT_TOKEN")
CHAT=os.environ.get("CHAT_ID")
IST=pytz.timezone("Asia/Kolkata")

# FULL F&O LIST - SOLARINDS + IDEA dono included
FNO = ["RELIANCE.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","BHARTIARTL.NS","ITC.NS","LT.NS","BAJFINANCE.NS","AXISBANK.NS","MARUTI.NS","SUNPHARMA.NS","TITAN.NS","ONGC.NS","TATAMOTORS.NS","ADANIENT.NS","ADANIPORTS.NS","POWERGRID.NS","NTPC.NS","COALINDIA.NS","HINDALCO.NS","JSWSTEEL.NS","CIPLA.NS","DIVISLAB.NS","EICHERMOT.NS","BAJAJ-AUTO.NS","BPCL.NS","INDUSINDBK.NS","TECHM.NS","M&M.NS","VEDL.NS","INDIGO.NS","ZOMATO.NS","DLF.NS","HAL.NS","BEL.NS","TATAPOWER.NS","PFC.NS","FEDERALBNK.NS","PNB.NS","BANKBARODA.NS","SOLARINDS.NS","IDEA.NS","PAYTM.NS","POLYCAB.NS","RVNL.NS","IRFC.NS","NHPC.NS","SJVN.NS","COALINDIA.NS","TATASTEEL.NS","INFY.NS","WIPRO.NS","HCLTECH.NS","LTIM.NS","PERSISTENT.NS","COFORGE.NS","MPHASIS.NS","TATACOMM.NS","INDUSINDBK.NS","BANDHANBNK.NS","IDFCFIRSTB.NS","PNB.NS","CANBK.NS","AUBANK.NS","MUTHOOTFIN.NS","CHOLAFIN.NS","PEL.NS","RECLTD.NS","IRCTC.NS","BSE.NS","MCX.NS","CDSL.NS","ANGELONE.NS","HDFCAMC.NS","ICICIPRULI.NS","SBILIFE.NS","HDFCLIFE.NS"]

def send(m):
    requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id":CHAT,"text":m,"parse_mode":"HTML"}, timeout=30)

def scan():
    now=datetime.now(IST).strftime("%d-%m %I:%M %p")
    bull=[]; bear=[]
    for sym in FNO:
        try:
            t=yf.Ticker(sym)
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

    bull=sorted(bull,key=lambda x:x[1],reverse=True)[:7]
    bear=sorted(bear,key=lambda x:x[1])[:7]

    if bull or bear:
        msg=f"🔥 <b>F&O SCAN - {now}</b>\n"
        if bull:
            msg+="🚀 <b>BULLISH:</b>\n"
            for s,p,c in bull:
                tag=" ⭐" if s in ["SOLARINDS","IDEA"] else ""
                msg+=f"• {s} {c:.1f} (+{p:.2f}%){tag}\n"
        if bear:
            msg+="\n🔻 <b>BEARISH:</b>\n"
            for s,p,c in bear:
                tag=" ⭐" if s in ["SOLARINDS","IDEA"] else ""
                msg+=f"• {s} {c:.1f} ({p:.2f}%){tag}\n"
        if any(s in ["SOLARINDS","IDEA"] for s,_,_ in bull+bear):
            msg+="\n✅ Tumhare wale stocks select hue!"
    else:
        msg=f"ℹ️ <b>Market - {now}</b>\n0.6%+ breakout nahi hai.\nSOLARINDS & IDEA dono scan hue - move nahi hai."
    send(msg)

scan()
