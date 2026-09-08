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
}

STOCKS = {
    "PHARMA": ["SUNPHARMA.NS","DIVISLAB.NS","CIPLA.NS","DRREDDY.NS","LUPIN.NS","LAURUSLABS.NS","AUROPHARMA.NS","IPCALAB.NS"],
    "AUTO": ["MARUTI.NS","TATAMOTORS.NS","M&M.NS","EICHERMOT.NS","BAJAJ-AUTO.NS"],
    "ENERGY": ["RELIANCE.NS","NTPC.NS","ONGC.NS","POWERGRID.NS"],
    "PVT BANK": ["HDFCBANK.NS","ICICIBANK.NS","KOTAKBANK.NS","AXISBANK.NS","INDUSINDBK.NS"],
    "FMCG": ["ITC.NS","HINDUNILVR.NS","NESTLEIND.NS"],
    "OIL AND GAS": ["RELIANCE.NS","ONGC.NS","BPCL.NS"],
    "IT": ["TCS.NS","INFY.NS","WIPRO.NS"],
    "METAL": ["TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS"],
    "REALTY": ["DLF.NS","GODREJPROP.NS"],
    "INFRA": ["LT.NS","BSE.NS","POLYCAB.NS"],
    "DEFENCE": ["HAL.NS","BEL.NS","SOLARINDS.NS","MAZDOCK.NS","BEML.NS","COCHINSHIP.NS"],
}

def send(msg):
    BOT = os.environ.get('BOT_TOKEN')
    CHAT = os.environ.get('CHAT_ID')
    if not BOT or not CHAT:
        return
    url = f"https://api.telegram.org/bot{BOT}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print(e)

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
    sorted_perf = sorted(perf.items(), key=lambda x: x[1], reverse=True)
    return sorted_perf[:2], perf # TOP 2

def check_3g_red_low_vol(df):
    if len(df) < 30:
        return False
    df = df.dropna()
    c1 = df.iloc[-4]
    c2 = df.iloc[-3]
    c3 = df.iloc[-2]
    c4 = df.iloc[-1]
    green1 = c1['Close'] > c1['Open']
    green2 = c2['Close'] > c2['Open']
    green3 = c3['Close'] > c3['Open']
    red = c4['Close'] < c4['Open']
    if not (green1 and green2 and green3 and red):
        return False
    avg_vol = (c1['Volume'] + c2['Volume'] + c3['Volume']) / 3
    if avg_vol == 0:
        return False
    low_vol = c4['Volume'] < (avg_vol * 0.85)
    if not low_vol:
        return False
    prev_close = df['Close'].iloc[-16]
    curr = df['Close'].iloc[-1]
    pct = ((curr - prev_close) / prev_close) * 100
    if pct < 0.5:
        return False
    return True, float(curr), float(pct)

def scan():
    now = datetime.now(IST).strftime("%d-%m %I:%M %p")
    try:
        top2, all_perf = get_top_sectors()
        sorted_perf = sorted(all_perf.items(), key=lambda x: x[1], reverse=True)
        perf_txt = "\n".join([f"{k}: {v:+.2f}%" for k, v in sorted_perf[:4]])

        if top2[0][1] < 0.1:
            send(f"ℹ️ <b>{now}</b> No sector up today\n{perf_txt}")
            return

        final_msg = f"🔥 <b>BREAKOUT {now}</b>\n{perf_txt}\n"
        found_any = False

        for sec_name, sec_pct in top2:
            SYMS = STOCKS.get(sec_name, [])
            if not SYMS:
                continue
            try:
                data = yf.download(SYMS, period="5d", interval="15m", group_by='ticker', progress=False, threads=True)
            except:
                continue

            bull = []
            for sym in SYMS:
                try:
                    df = data[sym] if len(SYMS) > 1 else data
                    if df.empty:
                        continue
                    res = check_3g_red_low_vol(df)
                    if not res:
                        continue
                    _, curr, pct = res
                    bull.append((sym.replace('.NS',''), curr, pct))
                except:
                    continue

            if bull:
                found_any = True
                final_msg += f"\n<b>TOP: {sec_name} ({sec_pct:+.2f}%) - 3G+Red Low Vol:</b>\n"
                for s, c, p in bull:
                    final_msg += f"• {s} {c:.0f} ({p:+.2f}%)\n"

        if not found_any:
            final_msg += f"\nNo 3G+Red setup in TOP 2 sectors"

        send(final_msg)

    except Exception as e:
        send(f"❌ Error {now}: {e}")

if __name__ == "__main__":
    scan()
