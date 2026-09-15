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
        return
    try:
        url = f"https://api.telegram.org/bot{BOT}/sendMessage"
        requests.post(url, data={"chat_id": CHAT, "text": msg}, timeout=10)
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
