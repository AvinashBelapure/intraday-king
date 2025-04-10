import streamlit as st
import pandas as pd
import yfinance as yf
import datetime
import time
import pytz
from threading import Thread

# ====== 1. APP SETUP ======
st.set_page_config(
    page_title="Intraday King", 
    page_icon="📈", 
    layout="wide"
)

# ====== 2. MARKET HOURS & TIMEZONE ======
IST = pytz.timezone('Asia/Kolkata')
MARKET_OPEN = datetime.time(9, 15)  # 9:15 AM IST
MARKET_CLOSE = datetime.time(15, 30) # 3:30 PM IST

# ====== 3. NIFTY 50 STOCKS (CUSTOMIZE HERE!) ======
STOCKS = {
    'RELIANCE.NS': 'Reliance',
    'TATASTEEL.NS': 'Tata Steel',
    'HDFCBANK.NS': 'HDFC Bank',
    'INFY.NS': 'Infosys',
    'ICICIBANK.NS': 'ICICI Bank',
    # Add more stocks as needed (format: 'SYMBOL.NS': 'Company Name')
}

# ====== 4. SIGNAL GENERATION LOGIC ======
def get_signals():
    signals = []
    for symbol, name in STOCKS.items():
        try:
            # Fetch 5-minute interval data
            data = yf.download(symbol, period="1d", interval="5m", progress=False)
            if len(data) > 1:
                last_close = data['Close'].iloc[-1]
                prev_close = data['Close'].iloc[-2]
                change_pct = ((last_close - prev_close) / prev_close) * 100
                
                # Simple signal rule (customize this!)
                signal = "BUY" if change_pct > 0.5 else "SELL" if change_pct < -0.5 else "HOLD"
                
                signals.append({
                    "Stock": name,
                    "Symbol": symbol,
                    "Price": f"₹{last_close:.2f}",
                    "Change (%)": f"{change_pct:.2f}%",
                    "Signal": signal,
                    "Last Updated": datetime.datetime.now(IST).strftime("%H:%M:%S")
                })
        except Exception as e:
            st.error(f"Error fetching {symbol}: {e}")
    return pd.DataFrame(signals)

# ====== 5. AUTO-REFRESH (EVERY 5 MINUTES) ======
def auto_refresh():
    while True:
        now = datetime.datetime.now(IST).time()
        if MARKET_OPEN <= now <= MARKET_CLOSE:  # Only refresh during market hours
            st.session_state.signals = get_signals()
        time.sleep(300)  # 300 seconds = 5 minutes

# ====== 6. INITIALIZE APP ======
if "signals" not in st.session_state:
    st.session_state.signals = get_signals()

# Start background thread for auto-refresh
if "thread" not in st.session_state:
    thread = Thread(target=auto_refresh)
    thread.daemon = True
    thread.start()
    st.session_state.thread = thread

# ====== 7. STREAMLIT UI ======
st.title("📊 Intraday King - Live Stock Signals")
st.markdown("Real-time Nifty 50 trading signals | Updates every 5 minutes")

# Disclaimer
st.warning("⚠️ Educational use only. Not financial advice.")

# Display signals with color-coding
def color_signal(val):
    color = "green" if val == "BUY" else "red" if val == "SELL" else "gray"
    return f"color: {color}"

st.dataframe(
    st.session_state.signals.style.applymap(color_signal, subset=["Signal"]),
    use_container_width=True
)

# Last update time
st.caption(f"Last update: {datetime.datetime.now(IST).strftime('%H:%M:%S')}")

# Manual refresh button
if st.button("🔄 Refresh Now"):
    st.session_state.signals = get_signals()
    st.rerun()
