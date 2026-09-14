print("BOT STARTED - checking holiday")
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
    "AUTO": ["MARUTI.NS","M&M.NS","TATAMOTORS.NS"],
    "ENERGY": ["RELIANCE.NS","NTPC.NS","ONGC.NS"],
    "PVT BANK": ["HDFCBANK.NS","ICICIBANK.NS","KOTAKBANK.NS"],
    "FMCG": ["ITC.NS","HINDUNILVR.NS"],
    "OIL AND GAS": ["RELIANCE.NS","ONGC.NS"],
    "IT": ["TCS.NS","INFY.NS","WIPRO.NS"],
    "METAL": ["TATASTEEL.NS","JSWSTEEL.NS"],
    "REALTY": ["DLF.NS","GODREJPROP.NS"],
    "INFRA": ["LT.NS","ADANIENT.NS","ADANIPORTS.NS","INDUSTOWER.NS","BSE.NS"],
    "DEFENCE": ["HAL.NS","BEL.NS","MAZDOCK.NS"],
    "TELECOM": ["BHARTIARTL.NS","INDUSTOWER.NS","IDEA.NS"],
    "FINTECH": ["PAYTM.NS","HDFCBANK.NS"],
}
def send(msg):
    BOT=os.environ.get('BOT_TOKEN'); CHAT=os.environ.get('CHAT_ID')
    print(f"DEBUG send: BOT={bool(BOT)} CHAT={bool(CHAT)} MSG={msg[:50]}")
    if not BOT or not CHAT:
        print("Missing secrets")
        return
    try:
        url=f"https://api.telegram.org/bot{str(BOT)}/sendMessage"
        r=requests.post(url,data={"chat_id":CHAT,"text":msg},timeout=10)
        print(f"Telegram: {r.status_code} {r.text[:200]}")
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
    except: pass
    if not perf: return [("DEFENCE",0)],perf
    return sorted(perf.items(),key=lambda x:x[1],reverse=True)[:2],perf

def check_3g_red_low_vol(df):
    if len(df)<30: return False
    df=df.dropna().copy()
    try:
        today=df.index[-1].date(); today_df=df[df.index.date==today]
        if len(today_df)<4: return False
        c1,c2,c3,c4=today_df.iloc[-4],today_df.iloc[-3],today_df.iloc[-2],today_df.iloc[-1]
        if not (c1['Close']>c1['Open'] and c2['Close']>c2['Open'] and c3['Close']>c3['Open'] and c4['Close']<c4['Open']): return False
        avg=(c1['Volume']+c2['Volume']+c3['Volume'])/3
        if avg==0 or c4['Volume']>=avg*0.85: return False
        pct=((df['Close'].iloc[-1]-df['Close'].iloc[-16])/df['Close'].iloc[-16])*100
        if pct<0.5: return False
        return True,float(df['Close'].iloc[-1]),float(pct)
    except: return False

def scan():
    now_dt=datetime.now(IST); now=now_dt.strftime("%d-%m %I:%M %p")
    print(f"Time check: {now_dt} weekday {now_dt.weekday()}")
    if now_dt.weekday()>=5:
        msg=f"Weekend {now} Market Closed"; print(msg); send(msg); return
    try:
        nifty=yf.download("^NSEI",period="2d",interval="1d",progress=False)
        if not nifty.empty:
            last=nifty.index[-1].date(); today=now_dt.date()
            print(f"NSE last={last} today={today}")
            if last!=today:
                msg=f"Holiday {now} Market Closed - NSE Holiday"; print(msg); send(msg); return
    except Exception as e: print(f"Holiday check fail {e}")
    try:
        top2,all_perf=get_top_sectors()
        print(f"Sectors: {all_perf}")
        sorted_perf=sorted(all_perf.items(),key=lambda x:x[1],reverse=True)
        txt="\n".join([f"{k}: {v:+.2f}%" for k,v in sorted_perf[:6]])
        if not top2 or top2[0][1]<0.10:
            send(f"Info {now} No sector up\n{txt}"); return
        msg=f"BREAKOUT {now}\n{txt}\n"; found=False
        for sec_name,sec_pct in top2:
            syms=STOCKS.get(sec_name,[])
            if not syms: continue
            try: data=yf.download(syms,period="5d",interval="15m",group_by='ticker',progress=False,threads=True)
            except: continue
            bull=[]
            for sym in syms:
                try:
                    df=data[sym] if len(syms)>1 else data
                    if df.empty: continue
                    res=check_3g_red_low_vol(df)
                    if not res: continue
                    _,curr,pct=res; bull.append((sym.replace('.NS',''),curr,pct))
                except: continue
            if bull:
                found=True; msg+=f"\nTOP: {sec_name} {sec_pct:+.2f}%\n"
                for s,c,p in bull: msg+=f"{s} {c:.0f} {p:+.2f}%\n"
        if not found: msg+="\nNo 3G+Red Today"
        send(msg)
    except Exception as e:
        print(f"Error {e}"); send(f"Error {now}: {e}")

if __name__=="__main__":
    scan()
