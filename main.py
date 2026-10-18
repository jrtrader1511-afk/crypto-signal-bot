import os
import time
import requests
import ccxt
import pandas as pd

Telegram credentials are configured securely in the cloud.

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PAIRS = ["BTC/USDT", "ETH/USDT"]
TIMEFRAME = "1m"

exchange = ccxt.binance({
"enableRateLimit": True,
"timeout": 20000,
})

def send_telegram(message):
if not TOKEN or not CHAT_ID:
print("Telegram credentials are not configured.")
return

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

try:
    response = requests.post(
        url,
        json={"chat_id": CHAT_ID, "text": message},
        timeout=15,
    )
    response.raise_for_status()
except requests.RequestException as error:
    print(f"Telegram send failed: {error}")

def analyze(pair):
candles = exchange.fetch_ohlcv(
pair,
timeframe=TIMEFRAME,
limit=100,
)

df = pd.DataFrame(
    candles,
    columns=["time", "open", "high", "low", "close", "volume"],
)

df["ema9"] = df["close"].ewm(span=9, adjust=False).mean()
df["ema21"] = df["close"].ewm(span=21, adjust=False).mean()

delta = df["close"].diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)

avg_gain = gain.ewm(
    alpha=1 / 14, min_periods=14, adjust=False
).mean()

avg_loss = loss.ewm(
    alpha=1 / 14, min_periods=14, adjust=False
).mean()

rs = avg_gain / avg_loss.where(avg_loss != 0)
df["rsi"] = 100 - (100 / (1 + rs))

# Use the latest completed candle, not the live candle.
row = df.iloc[-2]

price = float(row["close"])
ema9 = float(row["ema9"])
ema21 = float(row["ema21"])
rsi = float(row["rsi"])

if ema9 > ema21 and 50 < rsi < 70:
    signal = "🟢 BUY setup"
elif ema9 < ema21 and 30 < rsi < 50:
    signal = "🔴 SELL setup"
else:
    signal = "⚪ WAIT"

message = (
    f"📊 Crypto Market Analysis\n\n"
    f"Pair: {pair}\n"
    f"Timeframe: {TIMEFRAME}\n"
    f"Last completed candle: {pd.to_datetime(row['time'], unit='ms', utc=True)}\n"
    f"Price: {price:.8f}\n"
    f"EMA 9: {ema9:.8f}\n"
    f"EMA 21: {ema21:.8f}\n"
    f"RSI 14: {rsi:.2f}\n\n"
    f"Signal: {signal}\n\n"
    "Educational indicator signal only. Not a guaranteed trade."
)

return message

def main():
print("Crypto Signal Bot started.")

while True:
    try:
        for pair in PAIRS:
            try:
                message = analyze(pair)
                print(message)
                send_telegram(message)
            except Exception as error:
                print(f"Analysis failed for {pair}: {error}")

            time.sleep(2)

        # Check once per minute.
        time.sleep(60)

    except Exception as error:
        print(f"Bot error: {error}")
        time.sleep(15)

if name == "main":
main()
