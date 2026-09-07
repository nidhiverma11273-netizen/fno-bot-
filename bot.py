import yfinance as yf
import requests
import pytz
from datetime import datetime

BOT = "YOUR_BOT_TOKEN" # secrets se ayega
CHAT_ID = "YOUR_CHAT_ID"

IST = pytz.timezone('Asia/Kolkata')
SYMS_BY_SECTOR = {
    "DEFENCE": ["HAL.NS","BEL.NS","SOLARINDS.NS","BEML.NS","COCHINSHIP.NS","MAZDOCK.NS"],
    "TELECOM": ["IDEA.NS","BHARTIARTL.NS"],
    "CAPITAL": ["BSE.NS","POLYCAB.NS","KEI.NS","CESC.NS"],
    "BANK": ["HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","KOTAKBANK.NS"],
    "IT": ["TCS.NS","INFY.NS","WIPRO.NS"],
    "PHARMA": ["SUNPHARMA.NS","DIVISLAB.NS"]
}

# Sector ka index symbol
SECTOR_INDEX = {
    "DEFENCE": "^CNXDEFENCE", # yfinance pe nahi hai to stock avg se lenge
    "TELECOM": "^CNXTELECOM",
    "CAPITAL": "^CNXINFRA",
    "BANK": "^NSEBANK",
    "IT": "^CNXIT",
    "PHARMA": "^CNXPHARMA"
}

def send(m):
    requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id":CHAT_ID,"text":m,"parse_mode":"HTML"})

def scan():
    now = datetime.now(IST).strftime("%d-%m %I:%M %p")
    try:
        # 1. HAR SECTOR KA AVG NIKALO
        sector_perf = {}
        for sec, stocks in SYMS_BY_SECTOR.items():
            data = yf.download(stocks, period="2d", interval="15m", group_by='ticker', progress=False)
            pct_list = []
            for sym in stocks:
                try:
                    df = data[sym] if len(stocks)>1 else data
                    if len(df)<16: continue
                    df=df.dropna()
                    prev=df['Close'].iloc[-16]
                    curr=df['Close'].iloc[-1]
                    pct=((curr-prev)/prev)*100
                    pct_list.append(pct)
                except: continue
            if pct_list:
                sector_perf[sec] = sum(pct_list)/len(pct_list)

        # Top sector
        top_sector = max(sector_perf, key=sector_perf.get)
        top_pct = sector_perf[top_sector]

        if top_pct < 0.8: # agar koi sector 0.8% se up nahi hai to skip
            send(f"ℹ️ <b>{now}</b> No sector 0.8%+ up\n\nTop: {top_sector} {top_pct:+.2f}%")
            return

        # 2. TOP SECTOR KE HI STOCK SCAN KARO
        SYMS = SYMS_BY_SECTOR[top_sector]
        data = yf.download(SYMS, period="2d", interval="15m", group_by='ticker', progress=False)

        bull=[]
        for sym in SYMS:
            try:
                df = data[sym] if len(SYMS)>1 else data
                if df.empty or len(df)<2: continue
                df=df.dropna()
                prev_close=df['Close'].iloc[-16] if len(df)>=16 else df['Close'].iloc[0]
                curr=df['Close'].iloc[-1]
                low=df['Low'].tail(26).min()
                high=df['High'].tail(26).max()
                pct=((curr-prev_close)/prev_close)*100
                intra=((high-low)/low)*100 if low else 0
                if pct>=1.2 and pct<8: # sirf real breakout
                    bull.append((sym.replace('.NS',''),curr,pct,intra))
            except: continue

        if bull:
            msg=f"🔥 <b>BREAKOUT {now}</b>\n<b>TOP SECTOR: {top_sector} ({top_pct:+.2f}%)</b>\n\n"
            for s,c,p,i in sorted(bull,key=lambda x:x[2],reverse=True):
                msg+=f"• {s} {c:.0f} ({p:+.2f}% / {i:.1f}%)\n"
        else:
            msg=f"ℹ️ <b>{now}</b> No 1.2%+ breakout in TOP sector\n\nSector: {top_sector} ({top_pct:+.2f}%)"
        send(msg)
    except Exception as e:
        send(f"Error: {e}")

scan()
