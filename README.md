AutoEdge: NSE/BSE Trading Assistant
AutoEdge is a real-time trading tool for Indian stock markets (NSE/BSE), built with Streamlit for Python 3.13 on Kali Linux. It delivers actionable insights with a premium, trader-focused interface, making it impossible to ignore for intraday and swing traders.
Features

Live Market Data: Tracks NIFTY 50 (^NSEI) and top 50 NSE stocks (e.g., RELIANCE.NS) with 5-minute, hourly, or daily data via yfinance.
Technical Indicators: 
Candlestick charts with SMA50, EMA200, Bollinger Bands (20,2), and VWAP.
RSI (14) and MACD (12,26,9) for momentum and trend analysis.


Real-Time Alerts: Visual and sound notifications for RSI overbought/oversold, MACD crossovers, and price breakouts above/below SMA50.
Custom Watchlist: Add/remove tickers, persisted in ~/.streamlit/watchlist.json.
Market Screener: Displays top gainers, losers, and volume movers.
NIFTY 50 Tracking: Real-time index chart for market context.
Premium UI: Dark theme with gradient buttons, animated charts, hover effects, and tooltips.
Exportable Reports: Download CSV files for watchlist and trade signals (price, RSI, MACD, alerts).
LAN Access: Runs on 0.0.0.0:8501 for local network access.
Performance: Parallelized data fetching for watchlist using ThreadPoolExecutor.

Prerequisites

OS: Kali Linux
Python: 3.13
Virtual Environment: ~/pythonprojects/venv
Internet: Required for yfinance API calls

Setup

Clear System-Wide Packages:Remove residual numpy and pandas_ta to avoid conflicts:
pip3 uninstall pandas_ta numpy -y
sudo pip3 uninstall pandas_ta numpy -y
sudo rm -rf /home/kali/.local/lib/python3.13/site-packages/{numpy,pandas_ta}*
sudo rm -rf /usr/lib/python3/dist-packages/{numpy,pandas_ta}*


Activate Virtual Environment:
source ~/pythonprojects/venv/bin/activate


Install Dependencies:Run this command to install required packages:
pip install --force-reinstall streamlit==1.38.0 yfinance==0.2.43 plotly==5.24.0 pandas==2.2.2 pandas_ta==0.3.14b0 numpy==1.26.4 setuptools==69.5.1


Fix Permissions:Ensure project directory is writable:
sudo chown -R kali:kali ~/pythonprojects
chmod -R u+w ~/pythonprojects


Save Script:Save market_intel.py to ~/pythonprojects/market_intel.py using:
nano ~/pythonprojects/market_intel.py

Copy the script from the provided artifact (ID: cb6ad502-7257-45af-9a51-83ecc009d6d0).

Verify Environment:Check numpy version and path:
python -c "import numpy; print(numpy.__version__); print(numpy.__file__)"

Expected:
1.26.4
/home/kali/pythonprojects/venv/lib/python3.13/site-packages/numpy/__init__.py


Run the Application:Start Streamlit:
streamlit run market_intel.py --server.address 0.0.0.0 --server.port 8501


Local Access: http://localhost:8501
LAN Access: http://<your-local-ip>:8501 (find IP with hostname -I)



Usage

Select Ticker: Choose from top 50 NSE stocks (e.g., RELIANCE.NS) via dropdown.
Period: 1D (5-minute), 5D (hourly), or 1M (daily).
Watchlist: Add/remove tickers, persists across sessions, export as CSV.
Charts: View candlestick (SMA50, EMA200, Bollinger Bands, VWAP), RSI, MACD, volume, and NIFTY 50 index.
Alerts: Enable sound alerts for RSI, MACD, and price breakout signals.
Auto-Refresh: Updates every 30 seconds during market hours (9:15 AM–3:30 PM IST, Mon–Fri).
Reports: Download trade reports with price, RSI, MACD, and alerts.
LAN Access: Share with devices on your network.

Troubleshooting

Numpy Path Error:

Issue: numpy loaded from incorrect path.
Fix: Re-run dependency installation:pip install --force-reinstall numpy==1.26.4




Permission Issues:

Fix: Edit files without sudo and reset ownership:sudo chown -R kali:kali ~/pythonprojects




No Data for Ticker:

Fix: Verify ticker on Yahoo Finance. Clear cache:rm -rf ~/.streamlit/cache




LAN Access Issues:

Fix: Allow port 8501:sudo ufw allow 8501

Check IP:hostname -I




Dependency Errors:

Fix: Reinstall dependencies:pip install --force-reinstall streamlit==1.38.0 yfinance==0.2.43 plotly==5.24.0 pandas==2.2.2 pandas_ta==0.3.14b0 numpy==1.26.4 setuptools==69.5.1





Notes

Logging: Errors saved to ~/.streamlit/market_intel.log.
Limitations: yfinance may have slight delays; consider premium APIs for real-time data.
Performance: Optimized with caching and parallelized data fetching.

Support
For issues, share:
source ~/pythonprojects/venv/bin/activate
python -c "import numpy; print(numpy.__version__); print(numpy.__file__)"
pip list

Contact: [Insert contact or issue tracker if applicable].
Happy trading with AutoEdge! 🚀
