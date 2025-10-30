
import streamlit as st
import queue
import pandas as pd
import time
from bot import TradingBot
from backtest import backtest as run_backtest
from strategy import MeanReversionStrategy
from data_fetcher import fetch_data_from_yahoo
from datetime import datetime, timedelta

def main():
    st.title("Nifty 50 Mean Reversion Trading Bot")

    if 'bot' not in st.session_state:
        st.session_state.log_queue = queue.Queue()
        st.session_state.bot = TradingBot(st.session_state.log_queue)
        st.session_state.logs = ""

    st.sidebar.title("Navigation")
    app_mode = st.sidebar.selectbox("Choose the app mode", ["Live Trading", "Backtesting"])

    if app_mode == "Live Trading":
        # --- Live Trading UI ---
        st.header("API Credentials")
        api_key = st.text_input("API Key", type="password")
        api_secret = st.text_input("API Secret", type="password")
        client_code = st.text_input("Client Code")
        pin = st.text_input("PIN", type="password")
        totp_secret = st.text_input("TOTP Secret", type="password")

        st.header("Bot Controls")
        if st.button("Start Bot"):
            if api_key and api_secret and client_code and pin and totp_secret:
                st.session_state.bot.start_trading(api_key, api_secret, client_code, pin, totp_secret)
            else:
                st.warning("Please enter all API credentials.")

        if st.button("Stop Bot"):
            st.session_state.bot.stop_trading()

        st.header("Logs")
        log_container = st.empty()
        while not st.session_state.log_queue.empty():
            st.session_state.logs += st.session_state.log_queue.get() + "\n"

        log_container.text_area("Live Logs", st.session_state.logs, height=300)

        time.sleep(1)
        st.rerun()

    elif app_mode == "Backtesting":
        # --- Backtesting UI ---
        st.header("Backtesting")

        if st.button("Fetch Last 2 Years of Data from Yahoo Finance"):
            with st.spinner("Fetching data..."):
                # Fetch last 729 days of data to stay safely within Yahoo's 730-day limit for 1h interval
                start_date = (datetime.now() - timedelta(days=729)).strftime('%Y-%m-%d')
                end_date = datetime.now().strftime('%Y-%m-%d')
                price_data, vol_data, error = fetch_data_from_yahoo(start_date, end_date)
                if error:
                    st.error(error)
                else:
                    # Convert index to tz-naive to match the slider's output
                    if price_data is not None:
                        price_data.index = price_data.index.tz_localize(None)
                    st.session_state.price_data = price_data
                    st.session_state.vol_data = vol_data
                    st.success("Data fetched successfully!")
                    st.info("Using 1-hour data from Yahoo Finance as a proxy for the 4-hour strategy timeframe.")

        if 'price_data' in st.session_state:
            st.subheader("Select Date Range for Backtest")
            min_date = st.session_state.price_data.index.min().to_pydatetime()
            max_date = st.session_state.price_data.index.max().to_pydatetime()

            start_range, end_range = st.date_input(
                "Select the date range",
                (min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )

            if st.button("Run Backtest"):
                # Filter data based on the selected date range
                filtered_price_data = st.session_state.price_data[start_range:end_range]
                filtered_vol_data = None
                if 'vol_data' in st.session_state and st.session_state.vol_data is not None:
                    filtered_vol_data = st.session_state.vol_data[start_range:end_range]

                strategy = MeanReversionStrategy()
                trades = run_backtest(filtered_price_data, strategy, filtered_vol_data)
                st.write("Backtest Results:")
                st.dataframe(pd.DataFrame(trades))

if __name__ == "__main__":
    main()
