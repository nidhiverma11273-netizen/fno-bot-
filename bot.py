import yfinance as yf
import requests
import os
import pytz
from datetime import datetime
import pandas as pd

IST = pytz.timezone('Asia/Kolkata')

# Zerodha ke asli NSE Sector Indexes - yahi se +0.62% wala sahi ayega
SECTOR_INDEX = {
    "REALTY": "NIFTYREALTY.NS",
    "ENERGY": "NIFTYENERGY.NS", 
    "AUTO": "NIFTYAUTO.NS",
    "PVT BANK": "NIFTY_PVT_BANK.NS",
    "METAL": "NIFTYMETAL.NS",
    "MEDIA": "NIFTYMEDIA.NS",
    "PHARMA": "NIFTYPHARMA.NS",
    "IT": "NIFTYIT.NS",
    "FMCG": "NIFTYFMCG.NS",
    "INFRA": "NIFTYINFRA.NS",
    "PSU BANK": "NIFTYPSUBANK.NS",
    "OIL AND GAS": "CNXOIL.NS",
    "DEFENCE": "HAL.NS",
    "TELECOM": "BHARTIARTL.NS",
    "FINTECH": "PAYTM.NS"
}

# Fallback tickers for yfinance
SECTOR_FALLBACK = {
    "REALTY": "^CNXREALTY",
    "ENERGY": "^CNXENERGY",
    "AUTO": "^CNXAUTO",
    "PVT BANK": "^NSEBANK",
    "METAL": "^CNXMETAL",
    "MEDIA": "^CNXMEDIA",
    "PHARMA": "^CNXPHARMA",
    "IT": "^CNXIT",
    "FMCG": "^CNXFMCG",
    "INFRA": "^CNXINFRA",
    "PSU BANK": "^CNXPSUBANK",
    "OIL AND GAS": "^CNXOIL",
    "DEFENCE": "HAL.NS",
    "TELECOM": "BHARTIARTL.NS",
    "FINTECH": "PAYTM.NS"
}

STOCKS = {
    "PHARMA": ["SUNPHARMA.NS","DIVISLAB.NS","CIPLA.NS","LAURUSLABS.NS"],
    "AUTO": ["MARUTI.NS","M&M.NS","TATAMOTORS.NS","EICHERMOT.NS"],
    "ENERGY": ["RELIANCE.NS","NTPC.NS","ONGC.NS"],
    "PVT BANK": ["HDFCBANK.NS","ICICIBANK.NS","KOTAKBANK.NS","AXISBANK.NS"],
    "FMCG": ["ITC.NS","HINDUNILVR.NS","NESTLEIND.NS"],
    "OIL AND GAS": ["RELIANCE.NS","ONGC.NS"],
    "IT": ["TCS.NS","INFY.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS","LTIM.NS","PERSISTENT.NS"],
    "METAL": ["TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS"],
    "REALTY": ["DLF.NS","GODREJPROP.NS","OBEROIRLTY.NS","PRESTIGE.NS","LODHA.NS"],
    "INFRA": ["LT.NS","ADANIENT.NS","ADANIPORTS.NS","INDUSTOWER.NS","BSE.NS"],
    "DEFENCE": ["HAL.NS","BEL.NS","MAZDOCK.NS","COCHINSHIP.NS"],
    "TELECOM": ["BHARTIARTL.NS","INDUSTOWER.NS","IDEA.NS"],
    "FINTECH": ["PAYTM.NS","HDFCBANK.NS","BAJFINANCE.NS"],
    "MEDIA": ["ZEEL.NS","SUNTV.NS","PVRINOX.NS"],
    "PSU BANK": ["SBIN.NS","BANKBARODA.NS","PNB.NS"]
}

def send(msg):
    BOT = os.environ.get('BOT_TOKEN')
    CHAT = os.environ.get('CHAT_ID')
    if not BOT or not CHAT:
        return
    try:
        url = f"https://api.telegram.org/bot{BOT}/sendMessage"
        requests.post(url, data={"chat_id": CHAT, "text": msg}, timeout=15)
    except Exception as e:
        print(f"Send fail {e}")

def get_top_sector():
    """
    Zerodha jaisa asli NSE Sector Index % - Intraday Open vs LTP
    """
    perf = {}
    tickers = list(SECTOR_INDEX.values())
    try:
        # Pehle asli NSE indexes try karo
        data = yf.download(tickers, period="1d", interval="5m", group_by='ticker', progress=False, threads=True)
        for sec, ticker in SECTOR_INDEX.items():
            try:
                df = data[ticker] if len(tickers)>1 else data
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                df=df.dropna()
                if len(df)<2:
                    continue
                o=float(df['Open'].iloc[0])
                c=float(df['Close'].iloc[-1])
                if o==0: continue
                pct=((c-o)/o)*100
                perf[sec]=float(pct)
            except:
                continue
        # Jo fail hua uske liye fallback
        if len(perf)<3:
            fb_tickers = list(SECTOR_FALLBACK.values())
            data2 = yf.download(fb_tickers, period="1d", interval="5m", group_by='ticker', progress=False, threads=True)
            for sec, ticker in SECTOR_FALLBACK.items():
                if sec in perf: continue
                try:
                    df = data2[ticker] if len(fb_tickers)>1 else data2
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    df=df.dropna()
                    if len(df)<2: continue
                    o=float(df['Open'].iloc[0])
                    c=float(df['Close'].iloc[-1])
                    if o==0: continue
                    perf[sec]=float(((c-o)/o)*100)
                except:
                    continue
    except Exception as e:
        print(f"Sector fail {e}")
    if not perf:
        return [("REALTY",0)], perf
    top1 = sorted(perf.items(), key=lambda x:x[1], reverse=True)[:1]
    return top1, perf

def is_nifty_green():
    try:
        df = yf.download("^NSEI", period="1d", interval="5m", progress=False, threads=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df=df.dropna()
        today=datetime.now(IST).date()
        if not df.empty:
            tdf=df[df.index.date==today]
            if len(tdf)>=2:
                o=float(tdf['Open'].iloc[0])
                c=float(tdf['Close'].iloc[-1])
                return c>=o*0.998, o, c
        return True,0,0
    except Exception as e:
        return True,0,0

def check_1min_condition(df):
    """
    STRICT: Red candle ka volume aaj ki kisi bhi previous candle se kam
    """
    try:
        if isinstance(df.columns, pd.MultiIndex):
            df.columns=df.columns.get_level_values(0)
        df=df.dropna()
        today=datetime.now(IST).date()
        tdf=df[df.index.date==today].copy()
        if len(tdf)<=4:
            return False
        for idx in range(3, len(tdf)):
            candle=tdf.iloc[idx]
            is_red = float(candle['Close']) < float(candle['Open'])
            if not is_red: continue
            prev_vols = tdf.iloc[:idx]['Volume'].astype(float).values
            if len(prev_vols)<3: continue
            min_vol = float(pd.Series(prev_vols).min())
            curr_vol = float(candle['Volume'])
            if curr_vol < min_vol:
                day_open=float(tdf['Open'].iloc[0])
                day_low=float(tdf['Low'].min())
                open_low = abs(day_open-day_low)/day_open*100 < 0.25 if day_open!=0 else False
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
    if now_dt.weekday()>=5:
        send(f"Weekend {now} Market Closed"); return
    if now_dt.hour < 9 or (now_dt.hour==9 and now_dt.minute<15):
        return
    if now_dt.hour>15 or (now_dt.hour==15 and now_dt.minute>30):
        return
    try:
        nifty_d = yf.download("^NSEI", period="5d", interval="1d", progress=False, threads=False)
        if isinstance(nifty_d.columns, pd.MultiIndex):
            nifty_d.columns=nifty_d.columns.get_level_values(0)
        if not nifty_d.empty:
            last=nifty_d.index[-1].date()
            if (now_dt.date()-last).days>4:
                send(f"Holiday {now} NSE Closed"); return
    except:
        pass
    green, n_open, n_last = is_nifty_green()
    nifty_status = "GREEN" if green else "RED"
    top1, all_perf = get_top_sector()
    txt="\n".join([f"{k}: {v:+.2f}%" for k,v in sorted(all_perf.items(), key=lambda x:x[1], reverse=True)[:6]])
    msg=f"BREAKOUT {now} (1min) NIFTY {nifty_status}\n{txt}\n"
    sec_name, sec_pct = top1[0]
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
            ok, price, sig_time, open_low, vol, min_vol = res
            found=True
            tag=" [O=LOW ⭐]" if open_low else ""
            msg+=f"{sym.replace('.NS','')} {price:.0f} {sig_time} V{vol:.0f}<MIN{int(min_vol)}{tag}\n"
        except:
            continue
    if not found:
        msg+="\nNo Signal (1min)\nCond: 1st 3 ignore, Red Vol < MIN(All Prev Vol Today)"
    print(msg)
    send(msg)

if __name__=="__main__":
    scan()
