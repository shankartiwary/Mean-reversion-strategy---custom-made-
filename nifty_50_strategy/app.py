
import streamlit as st
import queue
import pandas as pd
import time
from bot import TradingBot
from backtest import backtest as run_backtest
from strategy import MeanReversionStrategy
from data_fetcher import fetch_data_from_yahoo
from performance import calculate_performance_metrics
from datetime import datetime, timedelta

def main():
    st.title("Nifty 50 Mean Reversion Trading Bot")

    # Initialize session state
    if 'bot' not in st.session_state:
        st.session_state.log_queue = queue.Queue()
        st.session_state.bot = TradingBot(st.session_state.log_queue)
        st.session_state.logs = ""
        st.session_state.price_data = None
        st.session_state.vol_data = None

    # Sidebar for navigation
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
        st.header("Backtesting")

        if st.button("Load or Fetch 20 Years of Data"):
            with st.spinner("Accessing data... This may take a moment the first time."):
                start_date = (datetime.now() - timedelta(days=20*365)).strftime('%Y-%m-%d')
                end_date = datetime.now().strftime('%Y-%m-%d')
                price_data, vol_data, message = fetch_data_from_yahoo(start_date, end_date)

                if message and "cache" in message:
                    st.success(message)
                elif message:
                    st.warning(message)

                if price_data is not None:
                    if price_data.index.tz is not None:
                        price_data.index = price_data.index.tz_localize(None)
                    if vol_data is not None and vol_data.index.tz is not None:
                        vol_data.index = vol_data.index.tz_localize(None)

                    st.session_state.price_data = price_data
                    st.session_state.vol_data = vol_data
                    st.success("Data is ready!")
                else:
                    st.error(message) # Show download error

        if st.session_state.price_data is not None:
            st.subheader("Select Date Range for Backtest")
            min_date = st.session_state.price_data.index.min().date()
            max_date = st.session_state.price_data.index.max().date()

            start_range, end_range = st.date_input(
                "Select the date range",
                (min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )

            if st.button("Run Backtest"):
                filtered_price_data = st.session_state.price_data[start_range:end_range]
                filtered_vol_data = None
                if st.session_state.vol_data is not None:
                    filtered_vol_data = st.session_state.vol_data.loc[str(start_range):str(end_range)]

                strategy = MeanReversionStrategy()
                trades = run_backtest(filtered_price_data, strategy, filtered_vol_data)

                st.subheader("Backtest Results")
                st.dataframe(pd.DataFrame(trades))

                if trades:
                    metrics = calculate_performance_metrics(trades, filtered_price_data)
                    st.subheader("Performance Metrics")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Return (%)", f"{metrics['Total Return (%)']:.2f}")
                    col2.metric("Win Ratio (%)", f"{metrics['Win Ratio (%)']:.2f}")
                    col3.metric("Sharpe Ratio", f"{metrics['Sharpe Ratio']:.2f}")

                    col4, col5, col6 = st.columns(3)
                    col4.metric("Winning Trades", metrics['Winning Trades'])
                    col5.metric("Losing Trades", metrics['Losing Trades'])
                    col6.metric("Max Drawdown", f"{metrics['Max Drawdown']:.2f}")

                    st.metric("Expectancy", f"{metrics['Expectancy']:.4f}")

if __name__ == "__main__":
    main()
