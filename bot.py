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
    "PSU BANK": "^CNXPSUBANK",
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
    "PVT BANK": ["HDFCBANK.NS","ICICIBANK.NS","KOTAKBANK.NS","AXISBANK.NS","SBIN.NS"],
    "PSU BANK": ["SBIN.NS","BANKBARODA.NS","PNB.NS","CANBK.NS","KOTAKBANK.NS"],
    "FMCG": ["ITC.NS","HINDUNILVR.NS","NESTLEIND.NS"],
    "OIL AND GAS": ["RELIANCE.NS","ONGC.NS"],
    "IT": ["TCS.NS","INFY.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS","LTIM.NS","PERSISTENT.NS"],
    "METAL": ["TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS"],
    "REALTY": ["DLF.NS","GODREJPROP.NS","OBEROIRLTY.NS"],
    "INFRA": ["LT.NS","ADANIENT.NS","ADANIPORTS.NS","INDUSTOWER.NS","BSE.NS"],
    "DEFENCE": ["HAL.NS","BEL.NS","MAZDOCK.NS","COCHINSHIP.NS"],
    "TELECOM": ["BHARTIARTL.NS","INDUSTOWER.NS","IDEA.NS"],
    "FINTECH": ["PAYTM.NS","BAJFINANCE.NS","ANGELONE.NS","BSE.NS","HDFCAMC.NS"]
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
        data = yf.download(tickers, period="1d", interval="1m", group_by='ticker', progress=False, threads=True)
        for sec, ticker in SECTOR_INDEX.items():
            try:
                df = data[ticker] if len(tickers)>1 else data
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                df=df.dropna()
                if len(df)<2: continue
                o = float(df['Open'].iloc[0])
                c = float(df['Close'].iloc[-1])
                if o==0: continue
                pct = ((c - o) / o)*100
                perf[sec]=float(pct)
            except: continue
        if not perf:
            d = yf.download(tickers, period="2d", interval="1d", group_by='ticker', progress=False, threads=True)
            for sec, ticker in SECTOR_INDEX.items():
                try:
                    df = d[ticker] if len(tickers)>1 else d
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    df=df.dropna()
                    if len(df)<2: continue
                    pct = ((float(df['Close'].iloc[-1]) - float(df['Close'].iloc[-2])) / float(df['Close'].iloc[-2]))*100
                    perf[sec]=float(pct)
                except: continue
    except Exception as e:
        print(f"Sector fail {e}")
    if not perf:
        return [("IT",0)], perf
    top1 = sorted(perf.items(), key=lambda x:x[1], reverse=True)[:1]
    return top1, perf

def to_ist(df):
    try:
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
        return df.tz_convert(IST)
    except:
        try:
            df.index = df.index.tz_convert(IST)
            return df
        except:
            return df

def check_zerodha_condition(df, debug_sym=""):
    """
    ZERODHA EXACT CONDITION:
    1. Pehli 3 candle GREEN (Close > Open)
    2. Uske baad koi RED candle jiska Volume pehle ki SABHI candle ke Volume se kam ho
    FIX: yfinance ka index UTC me aata hai, IST me convert karke date filter karna hai + 0 volume ignore
    """
    try:
        if isinstance(df.columns, pd.MultiIndex):
            df.columns=df.columns.get_level_values(0)
        df=df.dropna()
        df = to_ist(df)
        today=datetime.now(IST).date()
        tdf=df[df.index.date==today].copy()
        if len(tdf) <= 4:
            if debug_sym:
                print(f"{debug_sym} len {len(tdf)} <=4 skip")
            return False
        
        # Condition 1: Pehli 3 candle GREEN honi chahiye
        first3 = tdf.iloc[0:3]
        for i in range(3):
            c = first3.iloc[i]
            if float(c['Close']) <= float(c['Open']):
                if debug_sym=="HCLTECH.NS":
                    print(f"HCLTECH first3 fail at {i} O={c['Open']} C={c['Close']}")
                return False
        
        # Condition 2: 4th candle se Red dhoondo jiska Vol < MIN(All Prev Vol)
        for idx in range(3, len(tdf)):
            candle = tdf.iloc[idx]
            is_red = float(candle['Close']) < float(candle['Open'])
            if not is_red:
                continue
            
            prev_vols = tdf.iloc[0:idx]['Volume'].astype(float).values
            prev_vols = [v for v in prev_vols if v > 0]  # yfinance 09:15 pe 0 volume deta hai kabhi
            if len(prev_vols) < 3:
                continue
            
            min_vol = float(pd.Series(prev_vols).min())
            if min_vol == 0:
                continue
            curr_vol = float(candle['Volume'])
            
            if curr_vol < min_vol:
                day_open = float(tdf['Open'].iloc[0])
                day_low = float(tdf['Low'].min())
                open_low = abs(day_open - day_low) / day_open * 100 < 0.25 if day_open != 0 else False
                price = float(candle['Close'])
                sig_time = tdf.index[idx].strftime("%H:%M")
                return True, price, sig_time, open_low, curr_vol, min_vol
        if debug_sym=="HCLTECH.NS":
            print(f"HCLTECH no red low vol found till {len(tdf)} candles")
        return False
    except Exception as e:
        print(f"check fail {e} {debug_sym}")
        return False

def scan():
    now_dt=datetime.now(IST)
    now=now_dt.strftime("%d-%m %I:%M %p")
    print(f"Time {now_dt}")
    if now_dt.weekday()>=5:
        # Weekend - chup raho, raat ko message mat bhejo
        print(f"Weekend {now} - Skip")
        return
    if now_dt.hour < 9 or (now_dt.hour==9 and now_dt.minute<15):
        print("Before market - Skip")
        return
    if now_dt.hour>15 or (now_dt.hour==15 and now_dt.minute>30):
        print("After market - Skip")
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
                # Holiday hai to market time me bata do, raat ko chup raho
                if 9 <= now_dt.hour <= 15:
                    send(f"🏖️ Holiday {now} NSE Closed - No Trading Today")
                print(f"Holiday {now} NSE Closed")
                return
    except Exception as e:
        print(f"Holiday check fail {e}")

    try:
        df_n = yf.download("^NSEI", period="1d", interval="5m", progress=False, threads=False)
        if isinstance(df_n.columns, pd.MultiIndex):
            df_n.columns = df_n.columns.get_level_values(0)
        df_n=df_n.dropna()
        today=datetime.now(IST).date()
        tdf_n=df_n[df_n.index.date==today]
        if len(tdf_n)>=2:
            n_green = float(tdf_n['Close'].iloc[-1]) >= float(tdf_n['Open'].iloc[0])
            n_text = "GREEN" if n_green else "RED"
        else:
            n_text = "GREEN"
    except:
        n_text = "GREEN"

    top1, all_perf = get_top_sector()
    txt="\n".join([f"{k}: {v:+.2f}%" for k,v in sorted(all_perf.items(), key=lambda x:x[1], reverse=True)[:5]])
    msg=f"BREAKOUT {now} (1min) NIFTY {n_text}\n{txt}\n"
    sec_name, sec_pct = top1[0]
    msg+=f"\nTOP Sector: {sec_name} {sec_pct:+.2f}%\n"
    
    # FIX: TOP sector ke saath IT sector ko bhi hamesha scan karo (HCLTECH miss na ho)
    # Saare unique symbols ek baar me download
    all_syms = list(set(sum(STOCKS.values(), [])))
    # HCLTECH ko priority list me aage rakho
    if "HCLTECH.NS" in all_syms:
        all_syms.remove("HCLTECH.NS")
        all_syms = ["HCLTECH.NS"] + all_syms
    
    try:
        data=yf.download(all_syms, period="1d", interval="1m", group_by='ticker', progress=False, threads=True)
    except Exception as e:
        send(msg+"\nData fail "+str(e))
        return
    
    found=False
    # Pehle TOP sector wale check karo
    top_syms = STOCKS.get(sec_name, [])
    check_order = top_syms + [s for s in all_syms if s not in top_syms]
    
    for sym in check_order[:20]:  # Pehle 20 stocks check karo taki time bache
        try:
            df=data[sym] if len(all_syms)>1 else data
            if df.empty: continue
            debug = sym if sym=="HCLTECH.NS" else ""
            res=check_zerodha_condition(df, debug_sym=debug)
            if not res: continue
            ok, price, sig_time, open_low, vol, min_vol = res
            found=True
            tag=" [O=LOW ⭐]" if open_low else ""
            msg+=f"{sym.replace('.NS','')} {price:.0f} {sig_time} V{vol:.0f}<MIN{int(min_vol)} [3G]{tag}\n"
        except Exception as e:
            print(f"{sym} err {e}")
            continue
    if not found:
        msg+="\nNo Signal (1min)\nCond: 1st 3 GREEN + Red Vol < MIN(All Prev Vol)"
    print(msg)
    send(msg)

if __name__=="__main__":
    scan()
