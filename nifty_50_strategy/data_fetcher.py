
import yfinance as yf
import pandas as pd

def fetch_data_from_yahoo(start_date, end_date):
    """
    Fetches historical price data for Nifty 50 and volatility data for India VIX
    from Yahoo Finance.
    """
    try:
        # Fetch Nifty 50 data at a 1-hour interval as a proxy for the 4-hour strategy
        nifty_data = yf.download('^NSEI', start=start_date, end=end_date, interval='1h')
        if nifty_data.empty:
            return None, None, "No Nifty 50 data found for the selected date range."

        # Rename columns to match the backtester's requirements
        nifty_data.rename(columns={
            'Open': 'open', 'High': 'high', 'Low': 'low',
            'Close': 'close', 'Volume': 'volume'
        }, inplace=True)
        nifty_data.index.name = 'timestamp'

        # Fetch India VIX data
        vix_data = yf.download('^INDIAVIX', start=start_date, end=end_date)
        if vix_data.empty:
            return nifty_data, None, "Nifty 50 data fetched, but no India VIX data found."

        return nifty_data, vix_data['Close'], None
    except Exception as e:
        return None, None, f"An error occurred while fetching data: {e}"

if __name__ == '__main__':
    # Example usage
    start = '2023-01-01'
    end = '2024-01-01'
    price_data, vol_data, error = fetch_data_from_yahoo(start, end)
    if error:
        print(error)
    else:
        print("Nifty 50 Data:")
        print(price_data.head())
        print("\nIndia VIX Data:")
        print(vol_data.head())
