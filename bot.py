import os, requests, yfinance as yf
from datetime import datetime
import pytz

BOT=os.environ.get("BOT_TOKEN")
CHAT=os.environ.get("CHAT_ID")
IST=pytz.timezone("Asia/Kolkata")

SYMS = ["SOLARINDS.NS","IDEA.NS","RELIANCE.NS","HDFCBANK.NS","HAL.NS","BEL.NS","BSE.NS"]

def send(m):
    requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id":CHAT,"text":m,"parse_mode":"HTML"}, timeout=20)

def get_data(sym):
    try:
        t=yf.Ticker(sym)
        # 2 din ka 5m data lo
        df=t.history(period="5d", interval="15m", auto_adjust=False)
        if df.empty: return None,None,None,None
        # Aaj ka din
        today_df = df.tail(26) # aaj ke ~6.5 ghante
        if len(today_df)<2:
            today_df=df
        prev_close = df['Close'].iloc[-27] if len(df)>27 else df['Close'].iloc[0]
        curr = today_df['Close'].iloc[-1]
        low = today_df['Low'].min()
        high = today_df['High'].max()
        pct = ((curr-prev_close)/prev_close)*100
        intra = ((high-low)/low)*100
        return curr, pct, intra, prev_close
    except Exception as e:
        return None,None,None,None

def scan():
    now=datetime.now(IST).strftime("%d-%m %I:%M %p")
    bull=[]
    logs=[]
    for sym in SYMS:
        curr,pct,intra,prev = get_data(sym)
        if curr:
            logs.append(f"{sym.replace('.NS','')}: {curr:.0f} ({pct:+.2f}% / {intra:.2f}% intra) Prev {prev:.0f}")
            if pct>=1.2 or intra>=2.0:
                bull.append((sym.replace('.NS',''),curr,pct,intra))

    if bull:
        msg=f"🔥 <b>BREAKOUT {now}</b>\n\n"
        for s,c,p,i in sorted(bull,key=lambda x:x[2],reverse=True):
            msg+=f"• {s} {c:.0f} ({p:+.2f}% / Intra {i:.1f}%)\n"
        if any(s=="SOLARINDS" for s,_,_,_ in bull):
            msg+="\n✅ SOLARINDS ka chart wala breakout pakda!"
    else:
        msg=f"ℹ️ <b>{now}</b>\nNo 1.2%+ breakout\n\n"
        msg+="\n".join(logs[:7])

    send(msg)

scan()
