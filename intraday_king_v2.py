import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import pytz
from threading import Thread
import time

# App setup
st.set_page_config(
    page_title="Intraday King Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Market hours
IST = pytz.timezone('Asia/Kolkata')
MARKET_OPEN = datetime.time(9, 15)  # 9:15 AM IST
MARKET_CLOSE = datetime.time(15, 30)  # 3:30 PM IST

# Sample stocks (customize these)
STOCKS = {
    'RELIANCE.NS': 'Reliance Industries',
    'TCS.NS': 'Tata Consultancy Services',
    'HDFCBANK.NS': 'HDFC Bank'
}

def get_signal(data):
    """Improved signal generation logic"""
    if len(data) < 2:
        return "NO DATA"
    
    current_close = data['Close'].iloc[-1]
    prev_close = data['Close'].iloc[-2]
    change_pct = ((current_close - prev_close) / prev_close) * 100
    
    # Simple signal logic (customize this)
    if change_pct > 0.5:
        return "BUY"
    elif change_pct < -0.5:
        return "SELL"
    return "HOLD"

def fetch_stock_data(symbol):
    """Safe data fetching with error handling"""
    try:
        data = yf.download(
            symbol,
            period="1d",
            interval="5m",
            progress=False
        )
        if not data.empty:
            return data
    except Exception as e:
        st.error(f"Error fetching {symbol}: {str(e)}")
    return pd.DataFrame()

def get_signals():
    """Get signals for all stocks"""
    signals = []
    for symbol, name in STOCKS.items():
        data = fetch_stock_data(symbol)
        if not data.empty:
            signal = get_signal(data)
            signals.append({
                "Stock": name,
                "Symbol": symbol,
                "Price": data['Close'].iloc[-1],
                "Change (%)": ((data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100,
                "Signal": signal,
                "Last Updated": datetime.datetime.now(IST).strftime("%H:%M:%S")
            })
    return pd.DataFrame(signals)

# Auto-refresh logic
def auto_refresh():
    while True:
        now = datetime.datetime.now(IST).time()
        if MARKET_OPEN <= now <= MARKET_CLOSE:
            st.session_state.signals = get_signals()
        time.sleep(300)  # 5 minutes

# Initialize session state
if "signals" not in st.session_state:
    st.session_state.signals = get_signals()

# Start background thread
if "thread" not in st.session_state:
    thread = Thread(target=auto_refresh)
    thread.daemon = True
    thread.start()
    st.session_state.thread = thread

# UI Components
st.title("📈 Intraday King Pro")
st.markdown("Real-time trading signals for Indian stocks")

# Disclaimer
st.warning("""
⚠️ Educational use only. Not financial advice.
Data may be delayed by 15-20 minutes.
""")

# Display signals with color coding
def color_signal(val):
    if val == "BUY":
        return "background-color: green; color: white"
    elif val == "SELL":
        return "background-color: red; color: white"
    return ""

if not st.session_state.signals.empty:
    styled_df = st.session_state.signals.style.format({
        "Price": "{:.2f}",
        "Change (%)": "{:.2f}%"
    }).applymap(color_signal, subset=["Signal"])
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("Loading stock data... Please wait.")

# Last update time
st.caption(f"Last update: {datetime.datetime.now(IST).strftime('%H:%M:%S')}")

# Manual refresh button
if st.button("🔄 Refresh Now"):
    st.session_state.signals = get_signals()
    st.rerun()
