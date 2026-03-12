import os
import yfinance as yf
import matplotlib.pyplot as plt
import tweepy
from datetime import datetime
import talib  # For RSI

# -------------------
# API KEYS
# -------------------

API_KEY = os.environ["X_API_KEY"]
API_SECRET = os.environ["X_API_SECRET"]
ACCESS_TOKEN = os.environ["X_ACCESS_TOKEN"]
ACCESS_SECRET = os.environ["X_ACCESS_SECRET"]

client = tweepy.Client(
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_SECRET
)

auth = tweepy.OAuth1UserHandler(
    API_KEY,
    API_SECRET,
    ACCESS_TOKEN,
    ACCESS_SECRET
)

api = tweepy.API(auth)

# -------------------
# STOCKS
# -------------------

tickers = ["AAPL","MSFT","NVDA","AMZN","GOOGL","TSLA"]
data = yf.download(tickers, period="1y", group_by="ticker")

fig, axes = plt.subplots(2, 3, figsize=(16, 9))
axes = axes.flatten()

signals = []

for i, ticker in enumerate(tickers):

    df = data[ticker].copy()
    close = df["Close"]

    # Moving Averages
    ma50 = close.rolling(50, min_periods=1).mean()
    ma200 = close.rolling(200, min_periods=1).mean()

    # 52-week High/Low
    high_52 = close.rolling(252, min_periods=1).max()
    low_52 = close.rolling(252, min_periods=1).min()

    last_price = close.iloc[-1]

    # Distance to 52-week high
    distance_high = (last_price - high_52.iloc[-1]) / high_52.iloc[-1] * 100

    # Signals
    if last_price > ma50.iloc[-1]:
        signals.append(f"{ticker} above 50DMA")
    if last_price > ma200.iloc[-1]:
        signals.append(f"{ticker} above 200DMA")
    if abs(distance_high) < 5:
        signals.append(f"{ticker} near 52W high")

    # RSI
    rsi = talib.RSI(close, timeperiod=14)
    df['RSI'] = rsi

    # Plot Price and MAs
    axes[i].plot(close, label="Price", color='blue')
    axes[i].plot(ma50, label="MA50", linestyle='--', color='orange')
    axes[i].plot(ma200, label="MA200", linestyle='--', color='purple')

    # 52-week High/Low markers
    axes[i].scatter(high_52.index[-1], high_52.iloc[-1], color='green', s=100, marker='^', label='52w High')
    axes[i].scatter(low_52.index[-1], low_52.iloc[-1], color='red', s=100, marker='v', label='52w Low')

    # Optional: annotate RSI overbought/oversold
    if rsi.iloc[-1] > 70:
        axes[i].text(close.index[-1], last_price, 'RSI>70', color='red')
    elif rsi.iloc[-1] < 30:
        axes[i].text(close.index[-1], last_price, 'RSI<30', color='green')

    axes[i].set_title(ticker)
    axes[i].legend()
    axes[i].grid(True)

plt.tight_layout()

# Save chart
today = datetime.today().strftime("%Y-%m-%d")
filename = f"market_signals_{today}.png"
plt.savefig(filename)

# Prepare tweet
signal_text = "\n".join(signals[:6])
tweet_text = f"""
Market Signals — {today}

{signal_text}

Charts below ↓

#stocks #markets
"""

# Post tweet with media
media = api.media_upload(filename)
client.create_tweet(
    text=tweet_text,
    media_ids=[media.media_id]
)

print("Tweet posted successfully!")