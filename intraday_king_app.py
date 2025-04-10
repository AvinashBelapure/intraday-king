import streamlit as st
import pandas as pd
import yfinance as yf
import datetime
import pytz
from threading import Thread

# App setup
st.set_page_config(page_title="Intraday King", layout="wide")

# Time settings
IST = pytz.timezone('Asia/Kolkata')
MARKET_OPEN = datetime.time(9, 15)
MARKET_CLOSE = datetime.time(15, 30)

# Sample Nifty 50 stocks (expand if needed)
STOCKS = {
    'RELIANCE.NS': 'Reliance',
    'TATAMOTORS.NS': 'Tata Motors',
    'HDFCBANK.NS': 'HDFC Bank',
    'INFY.NS': 'Infosys',
    'ICICIBANK.NS': 'ICICI Bank'
}

# Generate fake signals (replace with real logic later)
def get_signals():
    signals = []
    for symbol, name in STOCKS.items():
        try:
            data = yf.download(symbol, period="1d", interval="5m", progress=False)
            if len(data) > 1:
                last_close = data['Close'][-1]
                prev_close = data['Close'][-2]
                change = ((last_close - prev_close) / prev_close) * 100
                
                # Simple signal logic (BUY if up, SELL if down)
                signal = "BUY" if change > 0.5 else "SELL" if change < -0.5 else "HOLD"
                
                signals.append({
                    "Stock": name,
                    "Symbol": symbol,
                    "Price": last_close,
                    "Change (%)": f"{change:.2f}%",
                    "Signal": signal,
                    "Time": datetime.datetime.now(IST).strftime("%H:%M:%S")
                })
        except:
            pass
    return pd.DataFrame(signals)

# Auto-refresh every 5 minutes
def auto_refresh():
    while True:
        now = datetime.datetime.now(IST).time()
        if MARKET_OPEN <= now <= MARKET_CLOSE:
            st.session_state.df = get_signals()
        time.sleep(300)  # 5 minutes

# Initialize
if 'df' not in st.session_state:
    st.session_state.df = get_signals()

# Start auto-refresh thread
if 'thread' not in st.session_state:
    thread = Thread(target=auto_refresh)
    thread.daemon = True
    thread.start()
    st.session_state.thread = thread

# --- UI ---
st.title("📈 Intraday King - FREE Live Signals")
st.markdown("**Real-time Nifty 50 stock signals** (Updates every 5 mins)")

# Disclaimer
st.warning("⚠️ Educational use only. Not financial advice.")

# Display signals
st.dataframe(st.session_state.df.style.applymap(
    lambda x: "color: green" if x == "BUY" else "color: red" if x == "SELL" else "color: gray",
    subset=["Signal"]
))

# Last update time
st.caption(f"Last update: {datetime.datetime.now(IST).strftime('%H:%M:%S')}")

# Manual refresh button
if st.button("🔄 Refresh Now"):
    st.session_state.df = get_signals()
    st.rerun()
