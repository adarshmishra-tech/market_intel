import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import pandas_ta as ta
from datetime import datetime, time
import pytz
import time as tm
import os
import logging
import socket
import numpy as np

# Set up logging
log_dir = os.path.expanduser("~/.streamlit")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'market_intel.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Check dependencies
try:
    import streamlit
    import yfinance
    import plotly
    import pandas
    import pandas_ta
    import numpy
    if numpy.__version__.startswith('2'):
        logger.error("numpy version 2.x detected, which is incompatible with pandas_ta. Please use numpy==1.26.4")
        st.error("Error: Incompatible numpy version. Please run: pip install numpy==1.26.4")
        st.stop()
except ImportError as e:
    logger.error(f"Missing dependency: {str(e)}")
    st.error(f"Error: Missing dependency {str(e)}. Please install requirements using: pip install -r requirements.txt")
    st.stop()

# Set Streamlit page config
try:
    st.set_page_config(page_title="MarketIntel: NSE/BSE Assistant", layout="wide", initial_sidebar_state="expanded")
except Exception as e:
    logger.error(f"Failed to set Streamlit page config: {str(e)}")
    st.error("Error initializing the application. Please check your Streamlit installation.")
    st.stop()

st.markdown("""
    <style>
        body { font-family: 'Roboto', sans-serif; }
        .stApp { background-color: #1A1A1A; color: #FFFFFF; }
        .css-1d391kg { background-color: #2A2A2A; padding: 15px; }
        .stButton>button { 
            background-color: #4CAF50; 
            color: white; 
            border-radius: 5px; 
            border: none; 
            padding: 8px 16px; 
            font-size: 14px; 
        }
        .stButton>button:hover { background-color: #45A049; }
        .stSelectbox>div>div { 
            background-color: #2A2A2A; 
            color: #FFFFFF; 
            border: 1px solid #4CAF50; 
            border-radius: 5px; 
        }
        .css-1v0mbdj { margin: 10px 0; }
        .css-1v0mbdj:hover { transform: scale(1.02); transition: transform 0.2s; }
        h1 { color: #4CAF50; font-size: 24px; margin-bottom: 10px; }
        h2, h3 { color: #4CAF50; font-size: 18px; margin-bottom: 8px; }
        .stMetric { background-color: #2A2A2A; border-radius: 5px; padding: 10px; }
        .tooltip { position: relative; display: inline-block; margin-left: 5px; }
        .tooltip .tooltiptext { 
            visibility: hidden; 
            background-color: #4CAF50; 
            color: #FFFFFF; 
            text-align: center; 
            border-radius: 5px; 
            padding: 8px; 
            position: absolute; 
            z-index: 1; 
            bottom: 125%; 
            left: 50%; 
            margin-left: -120px; 
            width: 240px; 
            opacity: 0; 
            transition: opacity 0.3s; 
        }
        .tooltip:hover .tooltiptext { visibility: visible; opacity: 1; }
        .watchlist-btn { 
            background: none; 
            border: none; 
            color: #4CAF50; 
            cursor: pointer; 
            font-size: 14px; 
            padding: 0; 
        }
        .watchlist-btn:hover { text-decoration: underline; }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'tickers' not in st.session_state:
    st.session_state.tickers = ['RELIANCE.NS', 'TATAMOTORS.NS', 'INFY.NS', 'HDFCBANK.NS', 'TCS.NS']
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = 'RELIANCE.NS'
if 'refresh' not in st.session_state:
    st.session_state.refresh = True
if 'period' not in st.session_state:
    st.session_state.period = '1d'

# Top 50 NSE stocks for autocomplete
nse_stocks = [
    'RELIANCE.NS', 'TATAMOTORS.NS', 'INFY.NS', 'HDFCBANK.NS', 'TCS.NS', 'SBIN.NS', 'ICICIBANK.NS', 
    'HINDUNILVR.NS', 'ITC.NS', 'BHARTIARTL.NS', 'BAJFINANCE.NS', 'KOTAKBANK.NS', 'AXISBANK.NS', 
    'ASIANPAINT.NS', 'MARUTI.NS', 'LT.NS', 'SUNPHARMA.NS', 'TITAN.NS', 'HCLTECH.NS', 'WIPRO.NS',
    'ULTRACEMCO.NS', 'TECHM.NS', 'JSWSTEEL.NS', 'POWERGRID.NS', 'ONGC.NS', 'NTPC.NS', 'COALINDIA.NS',
    'GRASIM.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'BAJAJFINSV.NS', 'HEROMOTOCO.NS', 'DRREDDY.NS',
    'BRITANNIA.NS', 'CIPLA.NS', 'DIVISLAB.NS', 'EICHERMOT.NS', 'INDUSINDBK.NS', 'NESTLEIND.NS',
    'SBILIFE.NS', 'HDFCLIFE.NS', 'TATASTEEL.NS', 'BPCL.NS', 'HINDALCO.NS', 'SHREECEM.NS',
    'BAJAJ-AUTO.NS', 'M&M.NS', 'APOLLOHOSP.NS', 'DABUR.NS', 'UPL.NS', 'PIDILITIND.NS'
]

# IST time zone
ist = pytz.timezone('Asia/Kolkata')

# NSE/BSE trading hours (9:15 AM to 3:30 PM IST, Monday–Friday)
def is_market_open():
    try:
        now = datetime.now(ist)
        market_open = time(9, 15)
        market_close = time(15, 30)
        is_weekday = now.weekday() < 5
        is_open = market_open <= now.time() <= market_close and is_weekday
        return is_open, now
    except Exception as e:
        logger.error(f"Error checking market status: {str(e)}")
        return False, datetime.now(ist)

# Fetch stock data with caching
@st.cache_data(ttl=60)
def fetch_stock_data(ticker, period='1d', interval='5m'):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period, interval=interval)
        if data.empty:
            logger.warning(f"No data for {ticker}")
            return pd.DataFrame()
        logger.info(f"Successfully fetched data for {ticker}")
        return data
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {str(e)}")
        return pd.DataFrame()

# Placeholder for news fetching
@st.cache_data(ttl=300)
def fetch_live_news(ticker):
    logger.info(f"News fetching not implemented for {ticker}")
    return []

# Calculate indicators
def calculate_indicators(data):
    if data.empty:
        return data
    try:
        data = data.copy()
        data['SMA50'] = ta.sma(data['Close'], length=50)
        data['EMA200'] = ta.ema(data['Close'], length=200)
        data['RSI'] = ta.rsi(data['Close'], length=14)
        macd = ta.macd(data['Close'], fast=12, slow=26, signal=9)
        if macd is not None:
            data['MACD'] = macd['MACD_12_26_9']
            data['MACD_Signal'] = macd['MACDs_12_26_9']
            data['MACD_Hist'] = macd['MACDh_12_26_9']
        return data
    except Exception as e:
        logger.error(f"Error calculating indicators: {str(e)}")
        return data

# Fetch screener data with caching
@st.cache_data(ttl=60)
def fetch_screener_data(tickers, period='1d'):
    gainers = []
    losers = []
    volume_movers = []
    for ticker in tickers:
        try:
            data = fetch_stock_data(ticker, period=period)
            if not data.empty:
                latest = data.iloc[-1]
                prev = data.iloc[0]
                change = ((latest['Close'] - prev['Open']) / prev['Open']) * 100
                volume = latest['Volume']
                info = {'Ticker': ticker, 'Change (%)': round(change, 2), 'Volume': int(volume), 'Price': round(latest['Close'], 2)}
                if change > 0:
                    gainers.append(info)
                else:
                    losers.append(info)
                volume_movers.append(info)
        except Exception as e:
            logger.error(f"Error in screener for {ticker}: {str(e)}")
            continue
    gainers = sorted(gainers, key=lambda x: x['Change (%)'], reverse=True)[:5]
    losers = sorted(losers, key=lambda x: x['Change (%)'])[:5]
    volume_movers = sorted(volume_movers, key=lambda x: x['Volume'], reverse=True)[:5]
    return gainers, losers, volume_movers

# Create candlestick chart with SMA/EMA
def create_candlestick_chart(data, ticker):
    fig = go.Figure()
    if not data.empty:
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name=ticker,
            increasing_line_color='#4CAF50',
            decreasing_line_color='#FF4D4D'
        ))
        if 'SMA50' in data.columns and data['SMA50'].notna().any():
            fig.add_trace(go.Scatter(x=data.index, y=data['SMA50'], name='SMA50', line=dict(color='#FFD700')))
        if 'EMA200' in data.columns and data['EMA200'].notna().any():
            fig.add_trace(go.Scatter(x=data.index, y=data['EMA200'], name='EMA200', line=dict(color='#00BFFF')))
    fig.update_layout(
        title=f"{ticker} Price Chart <span class='tooltip'>ℹ️<span class='tooltiptext'>Candlestick chart with 50-day Simple Moving Average and 200-day Exponential Moving Average for trend analysis.</span></span>",
        xaxis_title="Time (IST)",
        yaxis_title="Price (INR)",
        template="plotly_dark",
        margin=dict(l=50, r=50, t=50, b=50),
        height=400,
        showlegend=True
    )
    return fig

# Create RSI chart
def create_rsi_chart(data, ticker):
    fig = go.Figure()
    if not data.empty and 'RSI' in data.columns and data['RSI'].notna().any():
        fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI', line=dict(color='#FFA500')))
        fig.add_hline(y=70, line_dash="dash", line_color="#FF4D4D", annotation_text="Overbought")
        fig.add_hline(y=30, line_dash="dash", line_color="#4CAF50", annotation_text="Oversold")
    fig.update_layout(
        title=f"{ticker} RSI (14) <span class='tooltip'>ℹ️<span class='tooltiptext'>Relative Strength Index (14): Measures momentum (0–100). Above 70: overbought; below 30: oversold.</span></span>",
        xaxis_title="Time (IST)",
        yaxis_title="RSI",
        template="plotly_dark",
        margin=dict(l=50, r=50, t=50, b=50),
        height=200
    )
    return fig

# Create MACD chart
def create_macd_chart(data, ticker):
    fig = go.Figure()
    if not data.empty and 'MACD' in data.columns and data['MACD'].notna().any():
        fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], name='MACD', line=dict(color='#00BFFF')))
        fig.add_trace(go.Scatter(x=data.index, y=data['MACD_Signal'], name='Signal', line=dict(color='#FFD700')))
        fig.add_trace(go.Bar(x=data.index, y=data['MACD_Hist'], name='Histogram', marker_color='#4CAF50'))
    fig.update_layout(
        title=f"{ticker} MACD (12,26,9) <span class='tooltip'>ℹ️<span class='tooltiptext'>Moving Average Convergence Divergence: Shows trend direction and momentum via MACD line, signal line, and histogram.</span></span>",
        xaxis_title="Time (IST)",
        yaxis_title="MACD",
        template="plotly_dark",
        margin=dict(l=50, r=50, t=50, b=50),
        height=200
    )
    return fig

# Create volume chart
def create_volume_chart(data, ticker):
    fig = go.Figure()
    if not data.empty:
        fig.add_trace(go.Bar(x=data.index, y=data['Volume'], marker_color='#4CAF50', name="Volume"))
    fig.update_layout(
        title=f"{ticker} Volume <span class='tooltip'>ℹ️<span class='tooltiptext'>Trading volume: Number of shares traded over time.</span></span>",
        xaxis_title="Time (IST)",
        yaxis_title="Volume",
        template="plotly_dark",
        margin=dict(l=50, r=50, t=50, b=50),
        height=200
    )
    return fig

# Main app
def main():
    try:
        # Header
        st.markdown("<h1>MarketIntel: NSE/BSE Trading Assistant</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-style: italic; color: #4CAF50;'>Data over noise, speed over clutter, clarity over chaos.</p>", unsafe_allow_html=True)

        # Display local IP for LAN access
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            st.markdown(f"<p style='color: #FFFFFF;'>Access on local network: <a href='http://{local_ip}:8501' style='color: #4CAF50;'>http://{local_ip}:8501</a></p>", unsafe_allow_html=True)
        except Exception as e:
            logger.error(f"Error getting local IP: {str(e)}")
            st.markdown("<p style='color: #FF4D4D;'>Could not detect local IP. Access via http://localhost:8501</p>", unsafe_allow_html=True)

        # Sidebar
        with st.sidebar:
            st.markdown("<h3>Control Panel</h3>", unsafe_allow_html=True)
            ticker_input = st.selectbox("Select NSE/BSE Ticker", nse_stocks, index=nse_stocks.index(st.session_state.selected_ticker) if st.session_state.selected_ticker in nse_stocks else 0, key="ticker_select")
            st.session_state.selected_ticker = ticker_input
            period = st.selectbox("Select Period", ["1d", "5d"], index=0 if st.session_state.period == '1d' else 1, key="period_select")
            st.session_state.period = period
            refresh_toggle = st.checkbox("Auto-Refresh (60s)", value=st.session_state.refresh, key="refresh_toggle")
            st.session_state.refresh = refresh_toggle
            st.markdown("<h3>Manage Watchlist</h3>", unsafe_allow_html=True)
            new_ticker = st.selectbox("Add Ticker", [''] + [t for t in nse_stocks if t not in st.session_state.tickers], index=0, key="add_ticker")
            if new_ticker:
                if new_ticker not in st.session_state.tickers:
                    st.session_state.tickers.append(new_ticker)
                    st.success(f"Added {new_ticker} to watchlist")
                    logger.info(f"Added {new_ticker} to watchlist")
            if st.button("Clear Watchlist", key="clear_watchlist"):
                st.session_state.tickers = ['RELIANCE.NS', 'TATAMOTORS.NS', 'INFY.NS']
                st.success("Watchlist reset")
                logger.info("Watchlist reset")

        # Market status
        is_open, now = is_market_open()
        market_status = "Open" if is_open else "Closed"
        status_color = "#4CAF50" if is_open else "#FF4D4D"
        st.markdown(f"""
            <div style='background-color: #2A2A2A; padding: 10px; border-radius: 5px;'>
                <span class='tooltip'>Market Status: <span style='color: {status_color};'>{market_status}</span>
                    <span class='tooltiptext'>NSE/BSE: 9:15 AM–3:30 PM IST, Mon–Fri</span>
                </span> | IST: {now.strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        """, unsafe_allow_html=True)

        # Layout
        col1, col2 = st.columns([3, 2])

        # Stock data and charts
        with col1:
            st.markdown(f"<h2>{st.session_state.selected_ticker}</h2>", unsafe_allow_html=True)
            data = fetch_stock_data(st.session_state.selected_ticker, period=st.session_state.period, interval='5m' if st.session_state.period == '1d' else '1h')
            if not data.empty:
                data = calculate_indicators(data)
                latest = data.iloc[-1]
                prev = data.iloc[0]
                change = ((latest['Close'] - prev['Open']) / prev['Open']) * 100
                col_metric1, col_metric2 = st.columns(2)
                with col_metric1:
                    st.metric(
                        label="Current Price (INR)",
                        value=f"₹{latest['Close']:.2f}",
                        delta=f"{change:.2f}%",
                        delta_color="normal"
                    )
                with col_metric2:
                    st.metric(
                        label="Volume",
                        value=f"{int(latest['Volume']):,}"
                    )
                st.plotly_chart(create_candlestick_chart(data, st.session_state.selected_ticker), use_container_width=True)
                st.plotly_chart(create_rsi_chart(data, st.session_state.selected_ticker), use_container_width=True)
                st.plotly_chart(create_macd_chart(data, st.session_state.selected_ticker), use_container_width=True)
                st.plotly_chart(create_volume_chart(data, st.session_state.selected_ticker), use_container_width=True)
            else:
                st.warning(f"No data available for {st.session_state.selected_ticker}. Please select another ticker or check your connection.")

        # Watchlist and screener
        with col2:
            st.markdown("<h2>Watchlist</h2>", unsafe_allow_html=True)
            gainers, losers, volume_movers = fetch_screener_data(st.session_state.tickers, period='1d')
            all_data = gainers + losers + volume_movers
            watchlist_df = pd.DataFrame(all_data).drop_duplicates().sort_values('Ticker')

            if not watchlist_df.empty:
                st.markdown("<h3>Overview</h3>", unsafe_allow_html=True)
                for _, row in watchlist_df.iterrows():
                    if st.button(row['Ticker'], key=f"watchlist_{row['Ticker']}", help=f"Click to view {row['Ticker']} details"):
                        st.session_state.selected_ticker = row['Ticker']
                        st.rerun()
                    color = '#4CAF50' if row['Change (%)'] > 0 else '#FF4D4D'
                    st.markdown(f"<span style='color: {color}'>Change: {row['Change (%)']:.2f}% | Price: ₹{row['Price']:.2f} | Volume: {row['Volume']:,}</span>", unsafe_allow_html=True)
                
                csv = watchlist_df.to_csv(index=False)
                st.download_button(
                    label="Download Watchlist as CSV",
                    data=csv,
                    file_name=f"watchlist_{now.strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="download_csv"
                )
            else:
                st.write("Watchlist is empty. Add tickers to view data.")

            st.markdown("<h3>Top Gainers</h3>", unsafe_allow_html=True)
            gainers_df = pd.DataFrame(gainers)
            if not gainers_df.empty:
                st.dataframe(gainers_df.style.format({"Change (%)": "{:.2f}", "Price": "₹{:.2f}", "Volume": "{:,}"})
                            .set_properties(**{'background-color': '#2A2A2A', 'color': '#4CAF50'}))
            else:
                st.write("No gainers available.")

            st.markdown("<h3>Top Losers</h3>", unsafe_allow_html=True)
            losers_df = pd.DataFrame(losers)
            if not losers_df.empty:
                st.dataframe(losers_df.style.format({"Change (%)": "{:.2f}", "Price": "₹{:.2f}", "Volume": "{:,}"})
                            .set_properties(**{'background-color': '#2A2A2A', 'color': '#FF4D4D'}))
            else:
                st.write("No losers available.")

            st.markdown("<h3>Volume Movers</h3>", unsafe_allow_html=True)
            volume_df = pd.DataFrame(volume_movers)
            if not volume_df.empty:
                st.dataframe(volume_df.style.format({"Change (%)": "{:.2f}", "Price": "₹{:.2f}", "Volume": "{:,}"})
                            .set_properties(**{'background-color': '#2A2A2A', 'color': '#FFFFFF'}))
            else:
                st.write("No volume movers available.")

        # Auto-refresh
        if st.session_state.refresh and is_open:
            tm.sleep(1)
            st.rerun()

    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error(f"An unexpected error occurred: {str(e)}. Please check your internet connection or try restarting the app.")

if __name__ == "__main__":
    main()
