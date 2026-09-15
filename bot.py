import yfinance as yf
import requests
import os
import pytz
from datetime import datetime

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
        print("Missing secrets")
        return
    try:
        url = f"https://api.telegram.org/bot{BOT}/sendMessage"
        r = requests.post(url, data={"chat_id": CHAT, "text": msg}, timeout=15)
        print(f"Telegram {r.status_code}")
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
        df = yf.download("^NSEI", period="1d", interval="1m", progress=False)
        if df.empty:
            return True
        df = df.dropna()
        today = datetime.now(IST).date()
        tdf = df[df.index.date == today]
        if len(tdf) < 5:
            # 1d daily fallback
            d = yf.download("^NSEI", period="2d", interval="1d", progress=False)
            if len(d)>=1:
                return d['Close'].iloc[-1] > d['Open'].iloc[-1]
            return True
        day_open = tdf['Open'].iloc[0]
        day_last = tdf['Close'].iloc[-1]
        print(f"Nifty Open {day_open} Last {day_last} Green {day_last>day_open}")
        return day_last >= day_open
    except Exception as e:
        print(f"Nifty check fail {e}")
        return True

def check_condition_1min(df):
    """
    - Pehli 3 candle ignore
    - Uske baad jo bhi Red candle bane uska volume din ki sabhi pehle wali candle se kam ho
    - Open=Low check
    """
    try:
        if len(df) < 10:
            return False
        df = df.dropna()
        today = datetime.now(IST).date()
        tdf = df[df.index.date == today].copy()
        if len(tdf) < 8:
            return False
        # Pehli 3 candle ignore
        if len(tdf) <= 3:
            return False
        after_first_3 = tdf.iloc[3:]

        # Har Red candle check karo jo 3 ke baad aayi
        for idx in range(len(after_first_3)):
            real_idx = 3 + idx
            candle = tdf.iloc[real_idx]
            is_red = candle['Close'] < candle['Open']
            if not is_red:
                continue
            # Is red se pehle ki sabhi candle ki volume list
            prev_vols = tdf.iloc[:real_idx]['Volume'].values
            if len(prev_vols) < 4:
                continue
            min_vol = min(prev_vols)
            # Condition: Present Red Volume < din ki sabhi pehle candle se kam
            if candle['Volume'] < min_vol:
                # Open = Low check (0.15% tolerance)
                day_open = tdf['Open'].iloc[0]
                day_low = tdf['Low'].min()
                open_eq_low = abs(day_open - day_low) / day_open * 100 < 0.20
                # Current price
                curr = float(candle['Close'])
                # Time of signal
                sig_time = tdf.index[real_idx].strftime("%H:%M")
                return True, curr, sig_time, open_eq_low, float(candle['Volume']), float(min_vol)
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
            nifty = yf.download("^NSEI", period="5d", interval="1d", progress=False)
            if not nifty.empty:
                last = nifty.index[-1].date()
                today = now_dt.date()
                gap = (today - last).days
                if gap > 4:
                    send(f"Holiday {now} Market Closed")
                    return
        except:
            pass

    # Step 1: Nifty Green?
    if not is_nifty_green():
        print("Nifty not green, skip")
        # Fir bhi info bhejo
        send(f"Info {now} Nifty RED - No Trade\nNifty Green nahi hai isliye skip")
        return

    top1, all_perf = get_top_sectors()
    txt = "\n".join([f"{k}: {v:+.2f}%" for k,v in sorted(all_perf.items(), key=lambda x:x[1], reverse=True)[:6]])
    msg = f"BREAKOUT {now} (1min) NIFTY GREEN\n{txt}\n"
    found = False

    sec_name, sec_pct = top1[0]
    msg += f"\nTOP Sector: {sec_name} {sec_pct:+.2f}%\n"
    syms = STOCKS.get(sec_name, [])

    try:
        data = yf.download(syms, period="1d", interval="1m", group_by='ticker', progress=False, threads=True)
    except Exception as e:
        print(f"DL fail {e}")
        send(msg + "\nData fail")
        return

    for sym in syms:
        try:
            df = data[sym] if len(syms)>1 else data
            if df.empty:
                continue
            res = check_condition_1min(df)
            if not res:
                continue
            ok, curr, sig_time, open_low, vol, min_vol = res
            found = True
            tag = " [OPEN=LOW ⭐]" if open_low else ""
            msg += f"{sym.replace('.NS','')} {curr:.0f} {sig_time} Vol {vol:.0f}<{min_vol:.0f}{tag}\n"
        except Exception as e:
            print(f"{sym} fail {e}")
            continue

    if not found:
        msg += "\nNo Signal Today (1min)\nCond: 1st 3 candle ignore, Red Vol < All Prev Vol"

    print(msg)
    send(msg)

if __name__ == "__main__":
    scan()
