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

def get_top_sectors():
    perf = {}
    tickers = list(SECTOR_INDEX.values())
    try:
        data = yf.download(tickers, period="5d", interval="1d", group_by='ticker', progress=False, threads=True)
        for sec, ticker in SECTOR_INDEX.items():
            try:
                df = data[ticker] if len(tickers) > 1 else data
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                if len(df) < 2:
                    continue
                df = df.dropna()
                pct = ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
                perf[sec] = float(pct)
            except:
                continue
    except Exception as e:
        print(f"Sector fail {e}")
    if not perf:
        return [("IT",0)], perf
    return sorted(perf.items(), key=lambda x: x[1], reverse=True)[:1], perf

def is_nifty_green():
    try:
        df = yf.download("^NSEI", period="1d", interval="5m", progress=False, threads=False)
        if df.empty:
            return True
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna()
        today = datetime.now(IST).date()
        tdf = df[df.index.date == today]
        if len(tdf) < 2:
            # fallback daily
            d = yf.download("^NSEI", period="2d", interval="1d", progress=False, threads=False)
            if not d.empty:
                if isinstance(d.columns, pd.MultiIndex):
                    d.columns = d.columns.get_level_values(0)
                d = d.dropna()
                if len(d) >= 1:
                    o = float(d['Open'].iloc[-1])
                    c = float(d['Close'].iloc[-1])
                    print(f"Nifty Daily O {o} C {c}")
                    return c >= o
            return True
        o = float(tdf['Open'].iloc[0])
        c = float(tdf['Close'].iloc[-1])
        print(f"Nifty 1d O {o} L {c} Green {c>=o}")
        return c >= o
    except Exception as e:
        print(f"Nifty check fail {e}")
        return True

def check_condition_1min(df):
    try:
        if len(df) < 10:
            return False
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna()
        today = datetime.now(IST).date()
        tdf = df[df.index.date == today].copy()
        if len(tdf) < 8:
            return False
        if len(tdf) <= 3:
            return False
        # Pehli 3 ignore
        for real_idx in range(3, len(tdf)):
            candle = tdf.iloc[real_idx]
            try:
                is_red = float(candle['Close']) < float(candle['Open'])
            except:
                continue
            if not is_red:
                continue
            prev_vols = tdf.iloc[:real_idx]['Volume'].astype(float).values
            if len(prev_vols) < 4:
                continue
            min_vol = float(prev_vols.min())
            curr_vol = float(candle['Volume'])
            if curr_vol < min_vol:
                day_open = float(tdf['Open'].iloc[0])
                day_low = float(tdf['Low'].min())
                open_eq_low = abs(day_open - day_low) / day_open * 100 < 0.25 if day_open!=0 else False
                curr_price = float(candle['Close'])
                sig_time = tdf.index[real_idx].strftime("%H:%M")
                return True, curr_price, sig_time, open_eq_low, curr_vol, min_vol
        return False
    except Exception as e:
        print(f"check 1min fail {e}")
        return False

def scan():
    now_dt = datetime.now(IST)
    now = now_dt.strftime("%d-%m %I:%M %p")
    print(f"Time {now_dt}")
    if now_dt.weekday() >= 5:
        send(f"Weekend {now} Market Closed")
        return
    is_pre = now_dt.hour < 9 or (now_dt.hour==9 and now_dt.minute<15)
    if not is_pre:
        try:
            nifty = yf.download("^NSEI", period="5d", interval="1d", progress=False, threads=False)
            if isinstance(nifty.columns, pd.MultiIndex):
                nifty.columns = nifty.columns.get_level_values(0)
            if not nifty.empty:
                last = nifty.index[-1].date()
                today = now_dt.date()
                gap = (today - last).days
                if gap > 4:
                    send(f"Holiday {now} Market Closed")
                    return
        except Exception as e:
            print(f"Holiday check {e}")

    if not is_nifty_green():
        print("Nifty RED skip")
        send(f"Info {now} Nifty RED - No Trade")
        return

    top1, all_perf = get_top_sectors()
    txt = "\n".join([f"{k}: {v:+.2f}%" for k,v in sorted(all_perf.items(), key=lambda x:x[1], reverse=True)[:6]])
    msg = f"BREAKOUT {now} (1min) NIFTY GREEN\n{txt}\n"
    sec_name, sec_pct = top1[0]
    msg += f"\nTOP: {sec_name} {sec_pct:+.2f}%\n"
    syms = STOCKS.get(sec_name, [])
    try:
        data = yf.download(syms, period="1d", interval="1m", group_by='ticker', progress=False, threads=True)
    except Exception as e:
        print(f"DL fail {e}")
        send(msg + "\nData fail")
        return

    found=False
    for sym in syms:
        try:
            df = data[sym] if len(syms)>1 else data
            if df.empty:
                continue
            res = check_condition_1min(df)
            if not res:
                continue
            ok, curr, sig_time, open_low, vol, min_vol = res
            found=True
            tag = " [O=LOW ⭐]" if open_low else ""
            msg += f"{sym.replace('.NS','')} {curr:.0f} {sig_time} V{vol:.0f}<{min_vol:.0f}{tag}\n"
        except Exception as e:
            print(f"{sym} {e}")
            continue

    if not found:
        msg += "\nNo Signal (1min)\nCond: 1st3 ignore, Red Vol < All Prev Min"

    print(msg)
    send(msg)

if __name__ == "__main__":
    scan()
