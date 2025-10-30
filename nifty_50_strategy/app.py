
import streamlit as st
import queue
import pandas as pd
import time
from bot import TradingBot
from backtest import backtest as run_backtest
from strategy import MeanReversionStrategy

def main():
    st.title("Nifty 50 Mean Reversion Trading Bot")

    if 'bot' not in st.session_state:
        st.session_state.log_queue = queue.Queue()
        st.session_state.bot = TradingBot(st.session_state.log_queue)

    st.sidebar.title("Navigation")
    app_mode = st.sidebar.selectbox("Choose the app mode", ["Live Trading", "Backtesting"])

    if app_mode == "Live Trading":
        # UI for Live Trading
        # ... (same as before)

    elif app_mode == "Backtesting":
        st.header("Backtesting")

        # Data upload
        uploaded_file = st.file_uploader("Upload historical price data (CSV)", type="csv")
        volatility_file = st.file_uploader("Optional: Upload historical volatility data (CSV)", type="csv")

        if uploaded_file is not None:
            data = pd.read_csv(uploaded_file, index_col='timestamp', parse_dates=True)
            st.write("Price data loaded successfully:")
            st.write(data.head())

            volatility_data = None
            if volatility_file is not None:
                volatility_data = pd.read_csv(volatility_file, index_col='Date', parse_dates=True)['Close']
                st.write("Volatility data loaded successfully:")
                st.write(volatility_data.head())
            else:
                st.warning("No volatility data provided. Backtest will use a default value, which may affect accuracy.")

            if st.button("Run Backtest"):
                strategy = MeanReversionStrategy()
                trades = run_backtest(data, strategy, volatility_data)
                st.write("Backtest Results:")
                st.dataframe(pd.DataFrame(trades))

    if app_mode == "Live Trading":
        # UI for Live Trading
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
        logs = ""
        while not st.session_state.log_queue.empty():
            logs += st.session_state.log_queue.get() + "\n"

        log_container.text_area("Live Logs", logs, height=300)

        # Efficiently rerun the app to update logs
        time.sleep(1)
        st.rerun()

if __name__ == "__main__":
    main()
