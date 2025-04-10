import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import pytz
from threading import Thread
import time
import numpy as np

# App setup
st.set_page_config(
    page_title="Intraday King Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Market hours
IST = pytz.timezone('Asia/Kolkata')
MARKET_OPEN = datetime.time(9, 15)
MARKET_CLOSE = datetime.time(15, 30)

# Sample stocks
STOCKS = {
    'RELIANCE.NS': 'Reliance Industries',
    'TCS.NS': 'Tata Consultancy Services',
    'HDFCBANK.NS': 'HDFC Bank'
}

def get_signal(data):
    """Completely fixed signal generation"""
    if len(data) < 2:
        return "NO DATA"
    
    try:
        # Explicitly convert to float to avoid pandas comparison issues
        current_close = float(data['Close'].iloc[-1])
        prev_close = float(data['Close'].iloc[-2])
        change_pct = ((current_close - prev_close) / prev_close) * 100
        
        # Safe numerical comparison
        if change_pct > 0.5:
            return "BUY"
        elif change_pct < -0.5:
            return "SELL"
        return "HOLD"
    except Exception as e:
        st.error(f"Signal error: {str(e)}")
        return "ERROR"

def fetch_stock_data(symbol):
    """Robust data fetching"""
    try:
        data = yf.download(
            symbol,
            period="1d",
            interval="5m",
            progress=False
        )
        return data[~data.index.duplicated()]  # Remove duplicate timestamps
    except Exception as e:
        st.error(f"Failed to fetch {symbol}: {str(e)}")
        return pd.DataFrame()

def get_signals():
    """Error-proof signal generation"""
    signals = []
    for symbol, name in STOCKS.items():
        data = fetch_stock_data(symbol)
        if len(data) >= 2:  # Need at least 2 data points
            signal = get_signal(data)
            try:
                signals.append({
                    "Stock": name,
                    "Symbol": symbol,
                    "Price": float(data['Close'].iloc[-1]),
                    "Change (%)": float((data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2] * 100),
                    "Signal": signal,
                    "Last Updated": datetime.datetime.now(IST).strftime("%H:%M:%S")
                })
            except Exception as e:
                st.error(f"Processing error for {symbol}: {str(e)}")
    return pd.DataFrame(signals)

# Session state management
if "signals" not in st.session_state:
    st.session_state.signals = get_signals()

# Auto-refresh system
def auto_refresh():
    while True:
        now = datetime.datetime.now(IST).time()
        if MARKET_OPEN <= now <= MARKET_CLOSE:
            try:
                st.session_state.signals = get_signals()
            except Exception as e:
                st.error(f"Refresh failed: {str(e)}")
        time.sleep(300)  # 5 minutes

if "thread" not in st.session_state:
    thread = Thread(target=auto_refresh)
    thread.daemon = True
    thread.start()
    st.session_state.thread = thread

# UI Components
st.title("📈 Intraday King Pro")
st.markdown("**Fixed Version** | Real-time signals during market hours (9:15 AM - 3:30 PM IST)")

# Disclaimer
st.warning("""
⚠️ Educational use only. Not financial advice.
Data may be delayed by 15-20 minutes.
""")

# Display with error handling
try:
    if not st.session_state.signals.empty:
        st.dataframe(
            st.session_state.signals.style.format({
                "Price": "₹{:.2f}",
                "Change (%)": "{:.2f}%"
            }).applymap(
                lambda x: "color: green" if x == "BUY" else "color: red" if x == "SELL" else "",
                subset=["Signal"]
            ),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No data available - market may be closed")
except Exception as e:
    st.error(f"Display error: {str(e)}")

# Controls
col1, col2 = st.columns(2)
with col1:
    st.caption(f"Last update: {datetime.datetime.now(IST).strftime('%H:%M:%S')}")
with col2:
    if st.button("🔄 Manual Refresh"):
        st.session_state.signals = get_signals()
        st.rerun()
