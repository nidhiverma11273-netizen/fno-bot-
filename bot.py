print("BOT STARTED - 5min HCLTECH FIXED")
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
    "INFRA": "^CNXINFRA","DEFENCE": "HAL.NS","TELECOM": "BHARTIARTL.NS","FINTECH": "PAYTM.NS",
}
STOCKS = {
    "PHARMA": ["SUNPHARMA.NS","DIVISLAB.NS","CIPLA.NS","LAURUSLABS.NS","AUROPHARMA.NS"],
    "AUTO": ["MARUTI.NS","M&M.NS","TATAMOTORS.NS","EICHERMOT.NS","BAJAJ-AUTO.NS"],
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
    "FINTECH": ["PAYTM.NS","HDFCBANK.NS","BAJFINANCE.NS"],
}

def send(msg):
    BOT=os.environ.get('BOT_TOKEN'); CHAT=os.environ.get('CHAT_ID')
    print(f"Send: {msg[:200]}")
    if not BOT or not CHAT:
        print("Missing secrets")
        return
    try:
        url=f"https://api.telegram.org/bot{str(BOT)}/sendMessage"
        r=requests.post(url,data={"chat_id":CHAT,"text":msg},timeout=15)
        print(f"Telegram: {r.status_code}")
    except Exception as e:
        print(f"Send fail {e}")

def get_top_sectors():
    perf={}; tickers=list(SECTOR_INDEX.values())
    try:
        data=yf.download(tickers,period="5d",interval="1d",group_by='ticker',progress=False,threads=True)
        for sec,ticker in SECTOR_INDEX.items():
            try:
                df=data[ticker] if len(tickers)>1 else data
                if len(df)<2: continue
                df=df.dropna(); pct=((df['Close'].iloc[-1]-df['Close'].iloc[-2])/df['Close'].iloc[-2])*100
                perf[sec]=float(pct)
            except: continue
    except Exception as e:
        print(f"Sector fetch fail {e}")
    if not perf: return [("PVT BANK",0),("IT",0)],perf
    # TOP 4 kar diya taaki HCLTECH wala IT miss na ho
    return sorted(perf.items(),key=lambda x:x[1],reverse=True)[:4],perf

def check_3g_red_low_vol_5min(df):
    # KEWAL AAJ KI 5 MIN CANDLE
    if len(df)<10: return False
    df=df.dropna().copy()
    try:
        today = datetime.now(IST).date()
        today_df = df[df.index.date == today]
        if len(today_df) < 4:
            return False

        c1,c2,c3,c4 = today_df.iloc[-4], today_df.iloc[-3], today_df.iloc[-2], today_df.iloc[-1]

        # 3 Green + 1 Red
        cond = (c1['Close']>c1['Open'] and c2['Close']>c2['Open'] and c3['Close']>c3['Open'] and c4['Close']<c4['Open'])
        if not cond:
            return False

        # Volume loose kiya gap-up ke liye - 0.85
