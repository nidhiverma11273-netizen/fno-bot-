import yfinance as yf, requests, os, pytz
from datetime import datetime
BOT=os.environ.get("BOT_TOKEN"); CHAT=os.environ.get("CHAT_ID")
STOCKS=["ANGLEONE.NS","BSE.NS","CAMS.NS","CDSL.NS","360ONE.NS","RELIANCE.NS","TCS.NS"]
def send(m): requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage",data={"chat_id":CHAT,"text":m,"parse_mode":"Markdown"},timeout=20)
ist=pytz.timezone('Asia/Kolkata'); now=datetime.now(ist).strftime("%d-%m %I:%M %p")
found=[]
for s in STOCKS:
    try:
        d=yf.download(s,period="5d",interval="1d",progress=False,auto_adjust=True)
        if len(d)<2: continue
        pct=((float(d['Close'].iloc[-1])-float(d['Close'].iloc[-2]))/float(d['Close'].iloc[-2]))*100
        if pct>=0.8: found.append(f"✅ {s.replace('.NS','')}: {pct:.2f}%")
    except: pass
if found: send(f"🚀 *FNO Alert - {now}*\n\n"+"\n".join(found))
else: send(f"ℹ️ GitHub Bot LIVE! {now}")
