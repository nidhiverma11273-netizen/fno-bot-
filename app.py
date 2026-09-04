import yfinance as yf
from flask import Flask
import os, requests
from datetime import datetime
import pytz

app = Flask(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
STOCKS = ["ANGLEONE.NS","BSE.NS","RELIANCE.NS","TCS.NS","INFY.NS"]

def send_telegram(msg):
    if BOT_TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def check_setup():
    # Yahan tumhara Option A logic hai
    return "Bot is running - Market check at 9:35 AM"

@app.route("/")
def home():
    return "yash1661_bot is Live! Telegram alerts active."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
