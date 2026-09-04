import os, requests, yfinance as yf
from datetime import datetime
import pytz

BOT=os.environ.get("BOT_TOKEN")
CHAT=os.environ.get("CHAT_ID")
IST=pytz.timezone("Asia/Kolkata")

# NSE F&O List 2025 - Top 190 stocks
FNO_STOCKS = ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","BHARTIARTL.NS","ITC.NS","LT.NS","KOTAKBANK.NS","BAJFINANCE.NS","AXISBANK.NS","ASIANPAINT.NS","MARUTI.NS","WIPRO.NS","HCLTECH.NS","SUNPHARMA.NS","TITAN.NS","ULTRACEMCO.NS","ONGC.NS","TATAMOTORS.NS","TATASTEEL.NS","POWERGRID.NS","NTPC.NS","BAJAJFINSV.NS","ADANIENT.NS","ADANIPORTS.NS","COALINDIA.NS","HINDALCO.NS","JSWSTEEL.NS","GRASIM.NS","CIPLA.NS","DRREDDY.NS","DIVISLAB.NS","EICHERMOT.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS","BRITANNIA.NS","NESTLEIND.NS","HINDUNILVR.NS","BPCL.NS","INDUSINDBK.NS","SBILIFE.NS","HDFCLIFE.NS","ICICIPRULI.NS","APOLLOHOSP.NS","TECHM.NS","LTIM.NS","INFY.NS","M&M.NS","TATACONSUM.NS","UPL.NS","VEDL.NS","SAIL.NS","INDIGO.NS","ZOMATO.NS","PAYTM.NS","NYKAA.NS","POLYCAB.NS","HAVELLS.NS","VOLTAS.NS","DIXON.NS","DLF.NS","GODREJPROP.NS","OBEROIRLTY.NS","LODHA.NS","IRCTC.NS","HAL.NS","BEL.NS","BDL.NS","MAZAGON.NS","COCHINSHIP.NS","RVNL.NS","IRFC.NS","PFC.NS","RECLTD.NS","SJVN.NS","NHPC.NS","TATAPOWER.NS","ADANIGREEN.NS","ADANIENSOL.NS","TORNTPHARM.NS","ZYDUSLIFE.NS","LUPIN.NS","AUROPHARMA.NS","ALKEM.NS","BIOCON.NS","MANKIND.NS","JINDALSTEL.NS","NMDC.NS","HINDCOPPER.NS","NATIONALUM.NS","TATACHEM.NS","SRF.NS","DEEPAKNTR.NS","PIIND.NS","ATUL.NS","AARTIIND.NS","COROMANDEL.NS","CHAMBLFERT.NS","GNFC.NS","IPCALAB.NS","GLENMARK.NS","LAURUSLABS.NS","PERSISTENT.NS","COFORGE.NS","MPHASIS.NS","KPITTECH.NS","TATAELXSI.NS","OFSS.NS","BSOFT.NS","CYIENT.NS","LTTS.NS","FEDERALBNK.NS","IDFCFIRSTB.NS","BANDHANBNK.NS","PNB.NS","BANKBARODA.NS","CANBK.NS","AUBANK.NS","INDIANB.NS","UNIONBANK.NS","MUTHOOTFIN.NS","MANAPPURAM.NS","CHOLAFIN.NS","SHRIRAMFIN.NS","LICHSGFIN.NS","PEL.NS","LTF.NS","ABCAPITAL.NS","MFSL.NS","STARHEALTH.NS","ICICIGI.NS","GICRE.NS","NIACL.NS"]

def send(msg):
    url=f"https://api.telegram.org/bot{BOT}/sendMessage"
    requests.post(url,data={"chat_id":CHAT,"text":msg,"parse_mode":"HTML"},timeout=60)

def scan():
    bullish=[]
    bearish=[]
    now=datetime.now(IST).strftime("%d-%m %I:%M %p")

    for sym in FNO_STOCKS[:60]: # GitHub pe 60 stock scan karenge - 2 min me ho jayega, pura 190 karna ho to 60 hata dena
        try:
            df=yf.Ticker(sym).history(period="5d")
            if len(df)<2: continue
            prev=df['Close'].iloc[-2]
            curr=df['Close'].iloc[-1]
            pct=((curr-prev)/prev)*100
            vol_up = df['Volume'].iloc[-1] > df['Volume'].iloc[-2]*1.3

            if pct>1.5 and vol_up:
                bullish.append((sym.replace(".NS",""),pct,curr))
            elif pct<-1.5 and vol_up:
                bearish.append((sym.replace(".NS",""),pct,curr))
        except: continue

    bullish=sorted(bullish,key=lambda x:x[1],reverse=True)[:5]
    bearish=sorted(bearish,key=lambda x:x[1])[:5]

    msg=f"📊 <b>F&O SCAN - {now}</b>\nNifty Stocks Scanned: {len(FNO_STOCKS[:60])}\n\n"

    if bullish:
        msg+="🚀 <b>BULLISH Breakout (>1.5% + Volume):</b>\n"
        for s,p,c in bullish:
            msg+=f"• {s}: {c:.1f} (+{p:.2f}%)\n"
    else:
        msg+="🚀 Bullish: Koi strong breakout nahi\n"

    msg+="\n"

    if bearish:
        msg+="🔻 <b>BEARISH Breakdown (<-1.5% + Volume):</b>\n"
        for s,p,c in bearish:
            msg+=f"• {s}: {c:.1f} ({p:.2f}%)\n"
    else:
        msg+="🔻 Bearish: Koi strong breakdown nahi\n"

    msg+=f"\n⏰ Next scan kal 9:35 AM auto ayega!"

    if not bullish and not bearish:
        msg=f"ℹ️ <b>F&O Sideways - {now}</b>\nAaj koi bhi F&O stock me 1.5% se bada Volume breakout nahi hai.\nKal 9:35 AM ko fir scan hoga! ✅"

    send(msg)

scan()
