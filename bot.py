import yfinance as yf
import requests
import os
import pytz
from datetime import datetime

IST = pytz.timezone('Asia/Kolkata')

# ========= TUMHARI WATCHLIST SECTOR INDEX =========
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
    "PHARMA": ["SUNPHARMA.NS","DIVISLAB.NS","CIPLA.NS","DRREDDY.NS","LUPIN.NS"],
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

def get_top_sector():
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
        return "DEFENCE", 0, {}
    top = max(perf, key=perf.get)
    return top, perf[top], perf

def scan():
    now = datetime.now(IST).strftime("%d-%m %I:%M %p")
    try:
        top_sec, top_pct, all_perf = get_top_sector()
        sorted_perf = sorted(all_perf.items(), key=lambda x: x[1], reverse=True)
        perf_txt = "\n".join([f"{k}: {v:+.2f}%" for k, v in sorted_perf[:3]])

        if top_pct < 0.1:
            send(f"ℹ️ <b>{now}</b> No sector up today\nTop: {top_sec} {top_pct:+.2f}%\n{perf_txt}")
            return

        SYMS = STOCKS.get(top_sec, STOCKS["DEFENCE"])
        data = yf.download(SYMS, period="5d", interval="15m", group_by='ticker', progress=False, threads=True)

        bull = []
        for sym in SYMS:
            try:
                df = data[sym] if len(SYMS) > 1 else data
                if df.empty or len(df) < 30:
                    continue
                df = df.dropna()
                if len(df) < 30:
                    continue

                # Teri condition: 3 Green + 1 Red Low Volume
                c1 = df.iloc[-4]
                c2 = df.iloc[-3]
                c3 = df.iloc[-2]
                c4 = df.iloc[-1]

                green1 = c1['Close'] > c1['Open']
                green2 = c2['Close'] > c2['Open']
                green3 = c3['Close'] > c3['Open']
                red = c4['Close'] < c4['Open']

                if not (green1 and green2 and green3 and red):
                    continue

                avg_vol = (c1['Volume'] + c2['Volume'] + c3['Volume']) / 3
                low_vol = c4['Volume'] < (avg_vol * 0.85)

                if not low_vol:
                    continue

                prev_close = df['Close'].iloc[-16]
                curr = df['Close'].iloc[-1]
                pct = ((curr - prev_close) / prev_close) * 100

                if pct < 0.5:
                    continue

                bull.append((sym.replace('.NS',''), float(curr), float(pct)))

            except:
                continue

        if bull:
            msg = f"🔥 <b>BREAKOUT {now}</b>\n<b>TOP SECTOR: {top_sec} ({top_pct:+.2f}%)</b>\n{perf_txt}\n\n<b>3 Green + Red Low Vol:</b>\n"
            for s, c, p in bull:
                msg += f"• {s} {c:.0f} ({p:+.2f}%)\n"
        else:
            msg = f"ℹ️ <b>{now}</b> No 3G+Red setup in TOP sector\n<b>TOP SECTOR: {top_sec} ({top_pct:+.2f}%)</b>\n{perf_txt}"

        send(msg)

    except Exception as e:
        send(f"❌ Error {now}: {e}")

if __name__ == "__main__":
    scan()
