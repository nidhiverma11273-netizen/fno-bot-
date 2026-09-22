import yfinance as yf
import requests
import os
import pytz
from datetime import datetime
import pandas as pd

IST = pytz.timezone('Asia/Kolkata')

# Sirf Zerodha wale asli NSE Sector Indexes
SECTOR_INDEX = {
    "ENERGY": "NIFTYENERGY.NS",
    "AUTO": "NIFTYAUTO.NS",
    "PVT BANK": "NIFTY_PVT_BANK.NS",
    "REALTY": "NIFTYREALTY.NS",
    "FMCG": "NIFTYFMCG.NS",
    "MEDIA": "NIFTYMEDIA.NS",
    "PHARMA": "NIFTYPHARMA.NS",
    "METAL": "NIFTYMETAL.NS",
    "PSU BANK": "NIFTYPSUBANK.NS",
    "IT": "NIFTYIT.NS",
    "INFRA": "NIFTYINFRA.NS"
}

FALLBACK = {
    "ENERGY": "^CNXENERGY",
    "AUTO": "^CNXAUTO",
    "PVT BANK": "^NSEBANK",
    "REALTY": "^CNXREALTY",
    "FMCG": "^CNXFMCG",
    "MEDIA": "^CNXMEDIA",
    "PHARMA": "^CNXPHARMA",
    "METAL": "^CNXMETAL",
    "PSU BANK": "^CNXPSUBANK",
    "IT": "^CNXIT",
    "INFRA": "^CNXINFRA"
}

STOCKS = {
    "PHARMA": ["SUNPHARMA.NS","DIVISLAB.NS","CIPLA.NS"],
    "AUTO": ["MARUTI.NS","M&M.NS","TATAMOTORS.NS","EICHERMOT.NS"],
    "ENERGY": ["RELIANCE.NS","NTPC.NS","ONGC.NS","POWERGRID.NS"],
    "PVT BANK": ["HDFCBANK.NS","ICICIBANK.NS","KOTAKBANK.NS","AXISBANK.NS"],
    "FMCG": ["ITC.NS","HINDUNILVR.NS","NESTLEIND.NS"],
    "IT": ["TCS.NS","INFY.NS","WIPRO.NS","HCLTECH.NS"],
    "METAL": ["TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS"],
    "REALTY": ["DLF.NS","GODREJPROP.NS","OBEROIRLTY.NS","LODHA.NS","PRESTIGE.NS"],
    "INFRA": ["LT.NS","ADANIENT.NS","ADANIPORTS.NS","BSE.NS"],
    "PSU BANK": ["SBIN.NS","BANKBARODA.NS","PNB.NS"],
    "MEDIA": ["ZEEL.NS","SUNTV.NS","PVRINOX.NS"]
}

def send(msg):
    BOT=os.environ.get('BOT_TOKEN'); CHAT=os.environ.get('CHAT_ID')
    if not BOT or not CHAT: return
    try:
        requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id":CHAT,"text":msg}, timeout=15)
    except: pass

def get_top_sector():
    perf={}
    tickers=list(SECTOR_INDEX.values())
    try:
        data=yf.download(tickers, period="1d", interval="5m", group_by='ticker', progress=False, threads=True)
        for sec, ticker in SECTOR_INDEX.items():
            try:
                df=data[ticker] if len(tickers)>1 else data
                if isinstance(df.columns, pd.MultiIndex): df.columns=df.columns.get_level_values(0)
                df=df.dropna()
                if len(df)<2: continue
                o=float(df['Open'].iloc[0]); c=float(df['Close'].iloc[-1])
                if o==0: continue
                perf[sec]=((c-o)/o)*100
            except: continue
        if len(perf)<5:
            fb=list(FALLBACK.values())
            data2=yf.download(fb, period="1d", interval="5m", group_by='ticker', progress=False, threads=True)
            for sec, ticker in FALLBACK.items():
                if sec in perf: continue
                try:
                    df=data2[ticker] if len(fb)>1 else data2
                    if isinstance(df.columns, pd.MultiIndex): df.columns=df.columns.get_level_values(0)
                    df=df.dropna()
                    if len(df)<2: continue
                    o=float(df['Open'].iloc[0]); c=float(df['Close'].iloc[-1])
                    perf[sec]=((c-o)/o)*100
                except: continue
    except Exception as e:
        print(f"Sector fail {e}")
    if not perf:
        return [("ENERGY",0)], perf
    top1=sorted(perf.items(), key=lambda x:x[1], reverse=True)[:1]
    return top1, perf

def is_nifty_green():
    try:
        df=yf.download("^NSEI", period="1d", interval="5m", progress=False, threads=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns=df.columns.get_level_values(0)
        df=df.dropna()
        today=datetime.now(IST).date()
        if not df.empty:
            tdf=df[df.index.date==today]
            if len(tdf)>=2:
                o=float(tdf['Open'].iloc[0]); c=float(tdf['Close'].iloc[-1])
                return c>=o*0.998, o, c
        return True,0,0
    except:
        return True,0,0

def check_1min_condition(df):
    try:
        if isinstance(df.columns, pd.MultiIndex): df.columns=df.columns.get_level_values(0)
        df=df.dropna()
        today=datetime.now(IST).date()
        tdf=df[df.index.date==today].copy()
        if len(tdf)<=4: return False
        for idx in range(3, len(tdf)):
            candle=tdf.iloc[idx]
            is_red=float(candle['Close']) < float(candle['Open'])
            if not is_red: continue
            prev_vols=tdf.iloc[:idx]['Volume'].astype(float).values
            if len(prev_vols)<3: continue
            min_vol=float(pd.Series(prev_vols).min())
            curr_vol=float(candle['Volume'])
            if curr_vol < min_vol:
                day_open=float(tdf['Open'].iloc[0])
                day_low=float(tdf['Low'].min())
                open_low=abs(day_open-day_low)/day_open*100 < 0.25 if day_open!=0 else False
                price=float(candle['Close'])
                sig_time=tdf.index[idx].strftime("%H:%M")
                return True, price, sig_time, open_low, curr_vol, min_vol
        return False
    except Exception as e:
        print(f"check fail {e}")
        return False

def scan():
    now_dt=datetime.now(IST)
    now=now_dt.strftime("%d-%m %I:%M %p")
    if now_dt.weekday()>=5: send(f"Weekend {now} Market Closed"); return
    if now_dt.hour<9 or (now_dt.hour==9 and now_dt.minute<15): return
    if now_dt.hour>15 or (now_dt.hour==15 and now_dt.minute>30): return
    green,_,_=is_nifty_green()
    nifty_status="GREEN" if green else "RED"
    top1, all_perf=get_top_sector()
    txt="\n".join([f"{k}: {v:+.2f}%" for k,v in sorted(all_perf.items(), key=lambda x:x[1], reverse=True)[:6]])
    msg=f"BREAKOUT {now} (1min) NIFTY {nifty_status}\n{txt}\n"
    sec_name, sec_pct=top1[0]
    msg+=f"\nTOP Sector: {sec_name} {sec_pct:+.2f}%\n"
    syms=STOCKS.get(sec_name, [])
    try:
        data=yf.download(syms, period="1d", interval="1m", group_by='ticker', progress=False, threads=True)
    except:
        send(msg+"\nData fail"); return
    found=False
    for sym in syms:
        try:
            df=data[sym] if len(syms)>1 else data
            if df.empty: continue
            res=check_1min_condition(df)
            if not res: continue
            ok, price, sig_time, open_low, vol, min_vol=res
            found=True
            tag=" [O=LOW ⭐]" if open_low else ""
            msg+=f"{sym.replace('.NS','')} {price:.0f} {sig_time} V{vol:.0f}<MIN{int(min_vol)}{tag}\n"
        except: continue
    if not found:
        msg+="\nNo Signal (1min)\nCond: 1st 3 ignore, Red Vol < MIN(All Prev Vol Today)"
    print(msg)
    send(msg)

if __name__=="__main__":
    scan()
