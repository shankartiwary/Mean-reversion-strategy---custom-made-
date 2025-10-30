
import yfinance as yf
import pandas as pd
import time
import os
from datetime import datetime, timedelta

CACHE_DIR = "data_cache"
PRICE_CACHE_FILE = os.path.join(CACHE_DIR, "price_data.csv")
VOL_CACHE_FILE = os.path.join(CACHE_DIR, "vol_data.csv")

def fetch_data_from_yahoo(start_date, end_date):
    """
    Fetches historical data from Yahoo Finance, using a local cache to avoid
    redownloading recent data.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)

    # Check if cached files exist and are recent (less than 1 day old)
    cache_is_valid = False
    if os.path.exists(PRICE_CACHE_FILE):
        last_mod_time = os.path.getmtime(PRICE_CACHE_FILE)
        if (time.time() - last_mod_time) / 3600 < 24:
            cache_is_valid = True

    if cache_is_valid:
        try:
            price_data = pd.read_csv(PRICE_CACHE_FILE, index_col='timestamp', parse_dates=True)
            vol_data = pd.read_csv(VOL_CACHE_FILE, index_col='Date', parse_dates=True)['Close']
            return price_data, vol_data, "Loaded data from cache."
        except Exception:
            # If cache is invalid or corrupt, proceed to download
            pass

    # --- If cache is not valid, download from Yahoo Finance ---
    for attempt in range(3):
        try:
            tickers = "^NSEI ^INDIAVIX"
            data = yf.download(tickers, start=start_date, end=end_date, interval='1d')

            if data.empty or ('^NSEI' not in data.columns.get_level_values(1) and len(data.columns) > 1):
                return None, None, "No Nifty 50 data found."

            # Extract and save price data
            price_data = data.loc[:, (slice(None), '^NSEI')]
            price_data.columns = price_data.columns.droplevel(1)
            price_data.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'}, inplace=True)
            price_data.index.name = 'timestamp'
            price_data.to_csv(PRICE_CACHE_FILE)

            # Extract and save volatility data
            vol_data = None
            error_msg = None
            if '^INDIAVIX' in data.columns.get_level_values(1):
                vol_data = data.loc[:, ('Close', '^INDIAVIX')].rename('Close')
                vol_data.index.name = 'Date'
                vol_data.to_csv(VOL_CACHE_FILE)
            else:
                error_msg = "Nifty 50 data fetched, but no India VIX data found."

            return price_data, vol_data, error_msg

        except Exception as e:
            if "YFRateLimitError" in str(e) and attempt < 2:
                time.sleep(5)
                continue
            return None, None, f"An error occurred: {e}"

    return None, None, "Failed to fetch data after multiple attempts."
