import yfinance as yf
import requests
import os
import pytz
from datetime import datetime
import pandas as pd

IST = pytz.timezone('Asia/Kolkata')

SECTOR_INDEX = {
    "PHARMA": "^CNXPHARMA",
    "AUTO": "^CNXAUTO",
    "ENERGY": "^CNXENERGY",
    "PVT BANK": "^NSEBANK",
    "FMCG": "^CNXFMCG",
    "OIL AND GAS": "^CNXOIL",
    "IT": "^CNXIT",
    "METAL": "^CNXMETAL",
    "REALTY": "^CNXREALTY",
    "INFRA": "^CNXINFRA",
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
    "REALTY": ["DLF.NS","GODREJPROP.NS","OBEROIRLTY.NS"],
    "INFRA": ["LT.NS","ADANIENT.NS","ADANIPORTS.NS","INDUSTOWER.NS","BSE.NS"],
    "DEFENCE": ["HAL.NS","BEL.NS","MAZDOCK.NS","COCHINSHIP.NS"],
    "TELECOM": ["BHARTIARTL.NS","INDUSTOWER.NS","IDEA.NS"],
    "FINTECH": ["PAYTM.NS","HDFCBANK.NS","BAJFINANCE.NS"]
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
    perf = {}
    tickers = list(SECTOR_INDEX.values())
    try:
        data = yf.download(tickers, period="5d", interval="1d", group_by='ticker', progress=False, threads=True)
        for sec, ticker in SECTOR_INDEX.items():
            try:
                df = data[ticker] if len(tickers)>1 else data
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                if len(df)<2:
                    continue
                df = df.dropna()
                pct = ((float(df['Close'].iloc[-1]) - float(df['Close'].iloc[-2])) / float(df['Close'].iloc[-2]))*100
                perf[sec]=float(pct)
            except:
                continue
    except Exception as e:
        print(f"Sector fail {e}")
    if not perf:
        return [("IT",0)], perf
    top1 = sorted(perf.items(), key=lambda x:x[1], reverse=True)[:1]
    return top1, perf

def is_nifty_green():
    try:
        df = yf.download("^NSEI", period="1d", interval="1m", progress=False, threads=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df=df.dropna()
        today=datetime.now(IST).date()
        if not df.empty:
            tdf=df[df.index.date==today]
            if len(tdf)>=2:
                o=float(tdf['Open'].iloc[0])
                c=float(tdf['Close'].iloc[-1])
                print(f"Nifty 1m O {o} C {c} Green {c>=o}")
                return c>=o*0.998, o, c
        d=yf.download("^NSEI", period="2d", interval="1d", progress=False, threads=False)
        if isinstance(d.columns, pd.MultiIndex):
            d.columns=d.columns.get_level_values(0)
        d=d.dropna()
        if not d.empty:
            o=float(d['Open'].iloc[-1])
            c=float(d['Close'].iloc[-1])
            print(f"Nifty daily O {o} C {c}")
            return c>=o*0.999, o, c
        return True,0,0
    except Exception as e:
        print(f"Nifty check fail {e}")
        return True,0,0

def check_1min_condition(df):
    """
    STRICT CONDITION:
    - Pehli 3 candle ignore
    - RED candle ka volume aaj ki KISI BHI previous candle se kam hona chahiye = MIN
    - Sirf last 15 min me bana signal dikhayega, purana repeat nahi
    """
    try:
        if isinstance(df.columns, pd.MultiIndex):
            df.columns=df.columns.get_level_values(0)
        df=df.dropna()
        today=datetime.now(IST).date()
        tdf=df[df.index.date==today].copy()
        if len(tdf)<=4:
            return False
        # Only check last 15 candles to avoid repeat of morning signal
        start_idx = max(3, len(tdf)-15)
        # First find MIN of all prev volumes for strict check, but only signal if recent
        for idx in range(len(tdf)-1, start_idx-1, -1):  # reverse: latest first
            candle=tdf.iloc[idx]
            is_red = float(candle['Close']) < float(candle['Open'])
            if not is_red:
                continue
            prev_vols = tdf.iloc[:idx]['Volume'].astype(float).values
            if len(prev_vols)<3:
                continue
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

        # Pehli 3 ignore
        for idx in range(3, len(tdf)):
            candle=tdf.iloc[idx]
            is_red = float(candle['Close']) < float(candle['Open'])
            if not is_red:
                continue
            prev_vols = tdf.iloc[:idx]['Volume'].astype(float).values
            if len(prev_vols)<3:
                continue
            min_vol = float(pd.Series(prev_vols).min())
            curr_vol = float(candle['Volume'])
            # STRICT: Curr Vol < Sabhi Prev se kam
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
    print(f"Time {now_dt}")
    if now_dt.weekday()>=5:
        send(f"Weekend {now} Market Closed")
        return
    if now_dt.hour < 9 or (now_dt.hour==9 and now_dt.minute<15):
        print(f"Pre-Market {now} Waiting")
        return
    if now_dt.hour>15 or (now_dt.hour==15 and now_dt.minute>30):
        print(f"Market Closed {now}")
        return
    try:
        nifty_d = yf.download("^NSEI", period="5d", interval="1d", progress=False, threads=False)
        if isinstance(nifty_d.columns, pd.MultiIndex):
            nifty_d.columns=nifty_d.columns.get_level_values(0)
        if not nifty_d.empty:
            last=nifty_d.index[-1].date()
            today=now_dt.date()
            gap=(today-last).days
            if gap>4:
                send(f"Holiday {now} NSE Closed")
                return
    except:
        pass
    green, n_open, n_last = is_nifty_green()
    if not green:
        send(f"Info {now} Nifty RED - No Trade")
        return
    top1, all_perf = get_top_sector()
    txt="\n".join([f"{k}: {v:+.2f}%" for k,v in sorted(all_perf.items(), key=lambda x:x[1], reverse=True)[:5]])
    msg=f"BREAKOUT {now} (1min) NIFTY GREEN\n{txt}\n"
    sec_name, sec_pct = top1[0]
    msg+=f"\nTOP Sector: {sec_name} {sec_pct:+.2f}%\n"
    syms=STOCKS.get(sec_name, [])
    try:
        data=yf.download(syms, period="1d", interval="1m", group_by='ticker', progress=False, threads=True)
    except Exception as e:
        send(msg+"\nData fail")
        return
    found=False
    for sym in syms:
        try:
            df=data[sym] if len(syms)>1 else data
            if df.empty:
                continue
            res=check_1min_condition(df)
            if not res:
                continue
            ok, price, sig_time, open_low, vol, min_vol = res
            found=True
            tag=" [O=LOW ⭐]" if open_low else ""
            msg+=f"{sym.replace('.NS','')} {price:.0f} {sig_time} V{vol:.0f}<MIN{int(min_vol)} {tag}\n"
        except Exception as e:
            print(f"{sym} err {e}")
            continue
    if not found:
        msg+="\nNo Signal (1min)\nCond: 1st 3 ignore, Red Vol < MIN(All Prev Vol Today)"
    print(msg)
    send(msg)

if __name__=="__main__":
    scan()
