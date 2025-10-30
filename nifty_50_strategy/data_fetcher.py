
import yfinance as yf
import pandas as pd
import time

def fetch_data_from_yahoo(start_date, end_date):
    """
    Fetches historical price data for Nifty 50 and volatility data for India VIX
    from Yahoo Finance in a single API call, with a retry mechanism.
    """
    for attempt in range(3): # Try up to 3 times
        try:
            tickers = "^NSEI ^INDIAVIX"
            data = yf.download(tickers, start=start_date, end=end_date, interval='1d')

            if data.empty or '^NSEI' not in data.columns.get_level_values(1):
                return None, None, "No Nifty 50 data found for the selected date range."

            # Extract Nifty 50 data
            nifty_data = data.loc[:, (slice(None), '^NSEI')]
            nifty_data.columns = nifty_data.columns.droplevel(1)
            nifty_data.rename(columns={
                'Open': 'open', 'High': 'high', 'Low': 'low',
                'Close': 'close', 'Volume': 'volume'
            }, inplace=True)
            nifty_data.index.name = 'timestamp'

            # Extract India VIX data
            vol_data = None
            if '^INDIAVIX' in data.columns.get_level_values(1):
                vol_data = data.loc[:, ('Close', '^INDIAVIX')].rename('Close')
                vol_data.index.name = 'Date'

            error_msg = None
            if vol_data is None or vol_data.empty:
                error_msg = "Nifty 50 data fetched, but no India VIX data found."

            return nifty_data, vol_data, error_msg

        except Exception as e:
            if "YFRateLimitError" in str(e) and attempt < 2:
                time.sleep(5) # Wait 5 seconds before retrying
                continue
            return None, None, f"An error occurred after {attempt+1} attempts: {e}"
    return None, None, "Failed to fetch data after multiple attempts."


if __name__ == '__main__':
    # Example usage
    start = '2023-01-01'
    end = '2024-01-01'
    price_data, vol_data, error = fetch_data_from_yahoo(start, end)
    if error and not (price_data is not None and vol_data is None):
        print(error)
    else:
        print("Nifty 50 Data:")
        print(price_data.head())
        if vol_data is not None:
            print("\nIndia VIX Data:")
            print(vol_data.head())
        if error:
            print(f"\nNote: {error}")
