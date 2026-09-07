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

# ========= HAR SECTOR KE TOP STOCKS =========
STOCKS = {
    "PHARMA": ["SUNPHARMA.NS","DIVISLAB.NS","CIPLA.NS","DRREDDY.NS","LUPIN.NS","AUROPHARMA.NS"],
    "AUTO": ["MARUTI.NS","TATAMOTORS.NS","M&M.NS","EICHERMOT.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS"],
    "ENERGY": ["RELIANCE.NS","NTPC.NS","ONGC.NS","POWERGRID.NS","ADANIGREEN.NS","ADANIPOWER.NS"],
    "PVT BANK": ["HDFCBANK.NS","ICICIBANK.NS","KOTAKBANK.NS","AXISBANK.NS","INDUSINDBK.NS","IDFCFIRSTB.NS"],
    "FMCG": ["ITC.NS","HINDUNILVR.NS","NESTLEIND.NS","BRITANNIA.NS","DABUR.NS"],
    "OIL AND GAS": ["RELIANCE.NS","ONGC.NS","BPCL.NS","IOC.NS","GAIL.NS"],
    "IT": ["TCS.NS","INFY.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS"],
    "METAL": ["TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS","VEDL.NS","COALINDIA.NS"],
    "REALTY": ["DLF.NS","GODREJPROP.NS","OBEROIRLTY.NS","PRESTIGE.NS"],
    "INFRA": ["LT.NS","BSE.NS","POLYCAB.NS","KEI.NS","ULTRACEMCO.NS"],
    "DEFENCE": ["HAL.NS","BEL.NS","SOLARINDS.NS","MAZDOCK.NS","BEML.NS","COCHINSHIP.NS"],
}

def send(msg):
    BOT = os.environ.get('BOT_TOKEN')
    CHAT = os.environ.get('CHAT_ID')
    if not BOT or not CHAT:
        print("BOT_TOKEN / CHAT_ID missing")
        return
    url = f"https://api.telegram.org/bot{BOT}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

def get_top_sector():
    perf = {}
    tickers = list(SECTOR_INDEX.values())
    try:
        data = yf.download(tickers, period="5d", interval="1d", group_by='ticker', progress=False, threads=True)
        for sec, ticker in SECTOR_INDEX.items():
            try:
                if len(tickers) > 1:
                    df = data[ticker]
                else:
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
    except Exception as e:
        print(f"Sector download error: {e}")
    if not perf:
        return "PHARMA", 0, {}
    top = max(perf, key=perf.get)
    return top, perf[top], perf

def scan():
    now = datetime.now(IST).strftime("%d-%m %I:%M %p")
    try:
        top_sec, top_pct, all_perf = get_top_sector()

        # Ranking text top 3
        sorted_perf = sorted(all_perf.items(), key=lambda x: x[1], reverse=True)
        perf_txt = "\n".join([f"{k}: {v:+.2f}%" for k, v in sorted_perf[:3]])

        # Agar market band ya koi sector up nahi
        if top_pct < 0.1: # Monday ko 0.5 kar dena
            send(f"ℹ️ <b>{now}</b> No sector up today\nTop: {top_sec} {top_pct:+.2f}%\n{perf_txt}")
            return

        SYMS = STOCKS.get(top_sec, STOCKS["PHARMA"])
        data = yf.download(SYMS, period="2d", interval="15m", group_by='ticker', progress=False, threads=True)

        bull = []
        for sym in SYMS:
            try:
                df = data[sym] if len(SYMS) > 1 else data
                if df.empty or len(df) < 16:
                    continue
                df = df.dropna()
                if len(df) < 16:
                    continue
                prev_close = df['Close'].iloc[-16]
                curr = df['Close'].iloc[-1]
                low = df['Low'].tail(26).min()
                high = df['High'].tail(26).max()

                pct = ((curr - prev_close) / prev_close) * 100
                intra = ((high - low) / low) * 100 if low else 0

                if 1.2 <= pct < 8: # sirf real breakout
                    bull.append((sym.replace('.NS',''), float(curr), float(pct), float(intra)))
            except:
                continue

        if bull:
            msg = f"🔥 <b>BREAKOUT {now}</b>\n<b>TOP SECTOR: {top_sec} ({top_pct:+.2f}%)</b>\n{perf_txt}\n\n"
            for s, c, p, i in sorted(bull, key=lambda x: x[2], reverse=True):
                msg += f"• {s} {c:.0f} ({p:+.2f}% / {i:.1f}%)\n"
        else:
            msg = f"ℹ️ <b>{now}</b> No 1.2%+ breakout in TOP sector\n<b>TOP SECTOR: {top_sec} ({top_pct:+.2f}%)</b>\n{perf_txt}"

        send(msg)

    except Exception as e:
        send(f"❌ Error {now}: {e}")

if __name__ == "__main__":
    scan()
