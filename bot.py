import yfinance as yf, requests, pytz
from datetime import datetime
IST = pytz.timezone('Asia/Kolkata')

# 1. NSE KE SECTOR INDEX (Yahoo pe live hai)
SECTOR_INDEX = {
    "BANK": "^NSEBANK",
    "IT": "^CNXIT",
    "PHARMA": "^CNXPHARMA",
    "AUTO": "^CNXAUTO",
    "METAL": "^CNXMETAL",
    "FMCG": "^CNXFMCG",
    "ENERGY": "^CNXENERGY",
    "INFRA": "^CNXINFRA",
    "MEDIA": "^CNXMEDIA",
    "REALTY": "^CNXREALTY",
    "DEFENCE": "HAL.NS", # Defence ka index nahi hai, to HAL ko leader manenge
}

# 2. HAR SECTOR KE TOP STOCKS
STOCKS = {
    "BANK": ["HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","AXISBANK.NS","KOTAKBANK.NS"],
    "IT": ["TCS.NS","INFY.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS"],
    "PHARMA": ["SUNPHARMA.NS","DIVISLAB.NS","CIPLA.NS","DRREDDY.NS"],
    "AUTO": ["MARUTI.NS","TATAMOTORS.NS","M&M.NS","BAJAJ-AUTO.NS"],
    "METAL": ["TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS","VEDL.NS"],
    "FMCG": ["ITC.NS","HINDUNILVR.NS","NESTLEIND.NS"],
    "ENERGY": ["RELIANCE.NS","NTPC.NS","ONGC.NS","POWERGRID.NS"],
    "INFRA": ["LT.NS","BSE.NS","POLYCAB.NS","KEI.NS"],
    "MEDIA": ["ZEEL.NS","SUNTV.NS"],
    "REALTY": ["DLF.NS","GODREJPROP.NS","OBEROIRLTY.NS"],
    "DEFENCE": ["HAL.NS","BEL.NS","SOLARINDS.NS","MAZDOCK.NS","BEML.NS","COCHINSHIP.NS"],
}

def send(m):
    import os
    BOT=os.environ['BOT_TOKEN']; CHAT=os.environ['CHAT_ID']
    requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id":CHAT,"text":m,"parse_mode":"HTML"})

def get_top_sector():
    # Roz ka top sector index nikalo
    perf={}
    idx_list = list(SECTOR_INDEX.values())
    data = yf.download(idx_list, period="5d", interval="1d", group_by='ticker', progress=False)
    for sec, ticker in SECTOR_INDEX.items():
        try:
            df = data[ticker] if len(idx_list)>1 else data
            if len(df)<2: continue
            prev=df['Close'].iloc[-2]
            curr=df['Close'].iloc[-1]
            pct=((curr-prev)/prev)*100
            perf[sec]=pct
        except: continue
    # Sabse jyada up wala
    top = max(perf, key=perf.get)
    return top, perf[top], perf

def scan():
    now=datetime.now(IST).strftime("%d-%m %I:%M %p")
    try:
        top_sec, top_pct, all_perf = get_top_sector()

        # Agar koi sector 0.5% se bhi up nahi to mat bhejo
        if top_pct < 0.5:
            msg = f"ℹ️ <b>{now}</b> No sector up today\nTop: {top_sec} {top_pct:+.2f}%"
            send(msg); return

        # AB SIRF TOP SECTOR KE STOCKS SCAN
        SYMS = STOCKS[top_sec]
        data = yf.download(SYMS, period="2d", interval="15m", group_by='ticker', progress=False)
        bull=[]
        for sym in SYMS:
            try:
                df = data[sym] if len(SYMS)>1 else data
                if df.empty or len(df)<16: continue
                df=df.dropna()
                prev=df['Close'].iloc[-16]
                curr=df['Close'].iloc[-1]
                low=df['Low'].tail(26).min()
                high=df['High'].tail(26).max()
                pct=((curr-prev)/prev)*100
                intra=((high-low)/low)*100 if low else 0
                if 1.2 <= pct < 8:
                    bull.append((sym.replace('.NS',''),curr,pct,intra))
            except: continue

        # Message
        perf_txt = "\n".join([f"{k}: {v:+.2f}%" for k,v in sorted(all_perf.items(), key=lambda x:x[1], reverse=True)[:3]])
        if bull:
            msg=f"🔥 <b>BREAKOUT {now}</b>\n<b>TOP SECTOR: {top_sec} ({top_pct:+.2f}%)</b>\n{perf_txt}\n\n"
            for s,c,p,i in sorted(bull, key=lambda x:x[2], reverse=True):
                msg+=f"• {s} {c:.0f} ({p:+.2f}% / {i:.1f}%)\n"
        else:
            msg=f"ℹ️ <b>{now}</b> No 1.2%+ breakout\n<b>TOP SECTOR: {top_sec} ({top_pct:+.2f}%)</b>\n{perf_txt}"
        send(msg)
    except Exception as e:
        send(f"Error {now}: {e}")

scan()
