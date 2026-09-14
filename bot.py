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
    "FINTECH": "PAYTM.NS",
}

STOCKS = {
    "PHARMA": [
        "SUNPHARMA.NS",
        "DIVISLAB.NS",
        "CIPLA.NS",
        "LAURUSLABS.NS",
        "AUROPHARMA.NS"
    ],
    "AUTO": [
        "MARUTI.NS",
        "M&M.NS",
        "TATAMOTORS.NS"
    ],
    "ENERGY": [
        "RELIANCE.NS",
        "NTPC.NS",
        "ONGC.NS"
    ],
    "PVT BANK": [
        "HDFCBANK.NS",
        "ICICIBANK.NS",
        "KOTAKBANK.NS"
    ],
    "FMCG": [
        "ITC.NS",
        "HINDUNILVR.NS"
    ],
    "OIL AND GAS": [
        "RELIANCE.NS",
        "ONGC.NS"
    ],
    "IT": [
        "TCS.NS",
        "INFY.NS",
        "WIPRO.NS"
    ],
    "METAL": [
        "TATASTEEL.NS",
        "JSWSTEEL.NS"
    ],
    "REALTY": [
        "DLF.NS",
        "GODREJPROP.NS"
    ],
    "INFRA": [
        "LT.NS",
        "ADANIENT.NS",
        "ADANIPORTS.NS",
        "INDUSTOWER.NS",
        "BSE.NS"
    ],
    "DEFENCE": [
        "HAL.NS",
        "BEL.NS",
        "MAZDOCK.NS"
    ],
    "TELECOM": [
        "BHARTIARTL.NS",
        "INDUSTOWER.NS",
        "IDEA.NS"
    ],
    "FINTECH": [
        "PAYTM.NS",
        "HDFCBANK.NS"
    ],
}

def send(msg):
    BOT = os.environ.get('BOT_TOKEN')
    CHAT = os.environ.get('CHAT_ID')
    if not BOT or not CHAT:
        return
    try:
        tok = str(BOT)
        base = "https://api.telegram.org/bot"
        url = base + tok + "/sendMessage"
        requests.post(
            url,
            data={
                "chat_id": CHAT,
                "text": msg,
                "parse_mode": "HTML"
            },
            timeout=10
        )
    except Exception as e:
        print(e)

def get_top_sectors():
    perf = {}
    tickers = list(SECTOR_INDEX.values())
    try:
        data = yf.download(
            tickers,
            period="5d",
            interval="1d",
            group_by='ticker',
            progress=False,
            threads=True
        )
        for sec, ticker in SECTOR_INDEX.items():
            try:
                df = data[ticker]
                if len(tickers) == 1:
                    df = data
                if len(df) < 2:
                    continue
                df = df.dropna()
                prev = df['Close'].iloc[-2]
                curr = df['Close'].iloc[-1]
                pct = ((curr - prev) / prev) * 100
                perf[sec] = float(pct)
            except:
                continue
    except:
        pass
    if not perf:
        return [("DEFENCE", 0)], perf
    sorted_perf = sorted(
        perf.items(),
        key=lambda x: x[1],
        reverse=True
    )
    return sorted_perf[:2], perf

def check_3g_red_low_vol(df):
    if len(df) < 30:
        return False
    df = df.dropna().copy()
    try:
        today = df.index[-1].date()
        today_df = df[df.index.date == today]
        if len(today_df) < 4:
            return False
        c1 = today_df.iloc[-4]
        c2 = today_df.iloc[-3]
        c3 = today_df.iloc[-2]
        c4 = today_df.iloc[-1]
        g1 = c1['Close'] > c1['Open']
        g2 = c2['Close'] > c2['Open']
        g3 = c3['Close'] > c3['Open']
        r = c4['Close'] < c4['Open']
        if not (g1 and g2 and g3 and r):
            return False
        avg = (c1['Volume']+c2['Volume']+c3['Volume'])/3
        if avg == 0:
            return False
        if c4['Volume'] >= avg*0.85:
            return False
        prev = df['Close'].iloc[-16]
        curr = df['Close'].iloc[-1]
        pct = ((curr-prev)/prev)*100
        if pct < 0.5:
            return False
        return True, float(curr), float(pct)
    except:
        return False

def scan():
    now_dt = datetime.now(IST)
