import yfinance as yf
import requests
import os
import pytz
from datetime import datetime

IST = pytz.timezone('Asia/Kolkata')

SECTOR_INDEX = {
    "PHARMA": "^CNXPHARMA","AUTO": "^CNXAUTO","ENERGY": "^CNXENERGY",
    "PVT BANK": "^NSEBANK","FMCG": "^CNXFMCG","OIL AND GAS": "^CNXOIL",
    "IT": "^CNXIT","METAL": "^CNXMETAL","REALTY": "^CNXREALTY",
    "INFRA": "^CNXINFRA","DEFENCE": "HAL.NS","TELECOM": "BHARTIARTL.NS","FINTECH": "PAYTM.NS"
}

STOCKS = {
    "PHARMA": ["SUNPHARMA.NS","DIVISLAB.NS","CIPLA.NS"],
    "AUTO": ["MARUTI.NS","M&M.NS","TATAMOTORS.NS"],
    "ENERGY": ["RELIANCE.NS","NTPC.NS"],
    "PVT BANK": ["HDFCBANK.NS","ICICIBANK.NS","KOTAKBANK.NS"],
    "FMCG": ["ITC.NS","HINDUNILVR.NS"],
    "OIL AND GAS": ["RELIANCE.NS","ONGC.NS"],
    "IT": ["TCS.NS","INFY.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS","LTIM.NS"],
    "METAL": ["TATASTEEL.NS","JSWSTEEL.NS"],
    "REALTY": ["DLF.NS","GODREJPROP.NS"],
    "INFRA": ["LT.NS","ADANIENT.NS","ADANIPORTS.NS"],
    "DEFENCE": ["HAL.NS","BEL.NS"],
    "TELECOM": ["BHARTIARTL.NS"],
    "FINTECH": ["PAYTM.NS","BAJFINANCE.NS"]
}

def send(msg):
    BOT = os.environ.get('BOT_TOKEN')
    CHAT = os.environ.get('CHAT_ID')
    if not BOT or not CHAT:
        print("Missing secrets")
        return
    try:
        url = f"https://api.telegram.org/bot{BOT}/sendMessage"
        r = requests.post(url, data={"chat_id": CHAT, "text": msg}, timeout=10)
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
        return [("IT",0),("PVT BANK",0),("PHARMA",0),("AUTO",0)], perf
    return sorted(perf.items(), key=lambda x: x[1], reverse=True)[:4], perf

def check_3g_red(df):
    try:
        if len(df) < 10:
            return False
        df = df.dropna()
        today = datetime.now(IST).date()
        today_df = df[df.index.date == today]
        if len(today_df) < 4:
            return False
        c1 = today_df.iloc[-4]
        c2 = today_df.iloc[-3]
        c3 = today_df.iloc[-2]
        c4 = today_df.iloc[-1]
        if not (c1['Close']>c1['Open'] and c2['Close']>c2['Open'] and c3['Close']>c3['Open'] and c4['Close']<c4['Open']):
            return False
        avg = (c1['Volume']+c2['Volume']+c3['Volume'])/3
        if avg!=0 and c4['Volume'] >= avg*1.2:
            return False
        return True, float(c4['Close'])
    except:
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
                print(f"NSE last {last} today {today} gap {gap}")
                if gap > 4:
                    send(f"Holiday {now} Market Closed - NSE Holiday")
                    return
        except Exception as e:
            print(f"Holiday check {e}")

    top4, all_perf = get_top_sectors()
    txt = "\n".join([f"{k}: {v:+.2f}%" for k,v in sorted(all_perf.items(), key=lambda x:x[1], reverse=True)[:8]])
    msg = f"BREAKOUT {now} (5min)\n{txt}\n"
    found = False

    for sec_name, sec_pct in top4:
        syms = STOCKS.get(sec_name, [])
        if not syms:
            continue
        try:
            data = yf.download(syms, period="1d", interval="5m", group_by='ticker', progress=False, threads=True)
        except:
            continue
        bull = []
        for sym in syms:
            try:
                df = data[sym] if len(syms)>1 else data
                if df.empty:
                    continue
                res = check_3g_red(df)
                if not res:
                    continue
                ok, curr = res
                bull.append((sym.replace('.NS',''), curr))
            except:
                continue
        if bull:
            found = True
            msg += f"\nTOP: {sec_name} {sec_pct:+.2f}%\n"
            for s,c in bull:
                msg += f"{s} {c:.0f}\n"

    if not found:
        msg += "\nNo 3G+Red Today (5min)"

    print(msg)
    send(msg)

if __name__ == "__main__":
    scan()
