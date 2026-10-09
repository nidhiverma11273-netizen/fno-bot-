import yfinance as yf
import requests
import os
import pytz
from datetime import datetime
import pandas as pd

IST = pytz.timezone('Asia/Kolkata')

def send(msg):
    BOT = os.environ.get('BOT_TOKEN')
    CHAT = os.environ.get('CHAT_ID')
    try:
        url = f"https://api.telegram.org/bot{BOT}/sendMessage"
        requests.post(url, data={"chat_id": CHAT, "text": msg}, timeout=15)
    except Exception as e:
        print(f"Send fail {e}")

def debug_tcs():
    now_dt=datetime.now(IST)
    now=now_dt.strftime("%d-%m %I:%M %p")
    try:
        df = yf.download("TCS.NS", period="1d", interval="1m", progress=False, threads=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns=df.columns.get_level_values(0)
        df=df.dropna()
        today=datetime.now(IST).date()
        tdf=df[df.index.date==today].copy()
        
        msg=f"DEBUG TCS {now}\nLen:{len(tdf)}\n\nFirst 10 candles:\n"
        for i in range(min(10, len(tdf))):
            c=tdf.iloc[i]
            t=tdf.index[i].strftime("%H:%M")
            color="G" if float(c['Close'])>float(c['Open']) else "R"
            msg+=f"{t} {color} O:{float(c['Open']):.0f} C:{float(c['Close']):.0f} V:{int(float(c['Volume']))}\n"
        
        # Check first 3 GREEN
        first3=tdf.iloc[0:3]
        all_green = all(float(first3.iloc[i]['Close'])>float(first3.iloc[i]['Open']) for i in range(3))
        msg+=f"\n1st 3 GREEN? {all_green}\n"
        
        if len(tdf)>3:
            msg+="\nRed check (after 1st 3):\n"
            for idx in range(3, min(15, len(tdf))):
                candle=tdf.iloc[idx]
                is_red = float(candle['Close']) < float(candle['Open'])
                if not is_red:
                    continue
                prev_vols = tdf.iloc[0:idx]['Volume'].astype(float).values
                min_vol = float(pd.Series(prev_vols).min())
                curr_vol = float(candle['Volume'])
                t=tdf.index[idx].strftime("%H:%M")
                status = "PASS ✅" if curr_vol < min_vol else "FAIL ❌"
                msg+=f"{t} RED V{int(curr_vol)} < MIN{int(min_vol)} ? {status}\n"
        
        print(msg)
        send(msg)
    except Exception as e:
        send(f"DEBUG FAIL {e}")
        print(e)

if __name__=="__main__":
    debug_tcs()
