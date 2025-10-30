
from SmartApi import SmartConnect
from pyotp import TOTP
import config
from strategy import MeanReversionStrategy
import pandas as pd
import time

def get_live_volatility():
    # Placeholder for fetching live market volatility (e.g., from India VIX)
    # In a real implementation, you would fetch this from a reliable source.
    return 16  # Returning a mock value for now

def main():
    # Initialize the SmartAPI connection
    obj = SmartConnect(api_key=config.API_KEY)
    data = obj.generateSession(config.CLIENT_CODE, config.PIN, TOTP(config.TOTP_SECRET).now())

    if not data or data.get('status') is False or not data.get('data'):
        print("Authentication failed. Please check your credentials.")
        print(f"API Response: {data}")
        return

    refreshToken = data['data']['refreshToken']

    # Create an instance of the trading strategy
    strategy = MeanReversionStrategy()

    # Define the instrument and timeframe
    instrument_token = "99926000"  # NIFTY 50 index token
    timeframe = "FOUR_HOUR"

    in_trade = False
    entry_price = 0
    stop_loss = 0
    trade_direction = None

    while True:
        try:
            # Fetch historical data
            historical_data = get_historical_data(obj, instrument_token, timeframe)
            if historical_data is not None:
                # Generate trading signals
                signal = strategy.generate_signals(historical_data)
                print(f"Signal: {signal}")

                # Get the latest data
                latest_data = historical_data.iloc[-1]
                current_price = latest_data['close']
                ema = latest_data['ema']

                # --- Stop-Loss and Exit Logic ---
                if in_trade:
                    # Check for exit signal (price reaches EMA)
                    if strategy.get_exit_signal(current_price, ema, trade_direction):
                        print(f"Exit signal triggered at {current_price}. Exiting trade.")
                        in_trade = False
                        trade_direction = None
                    # Check for stop-loss
                    elif (trade_direction == 'BUY' and current_price <= stop_loss) or \
                         (trade_direction == 'SELL' and current_price >= stop_loss):
                        print(f"Stop-loss triggered at {current_price}. Exiting trade.")
                        in_trade = False
                        trade_direction = None

                # --- Entry Logic ---
                if not in_trade:
                    if signal == 'BUY' or signal == 'SELL':
                        in_trade = True
                        entry_price = current_price
                        trade_direction = signal
                        volatility = get_live_volatility()
                        stop_loss_value = strategy.get_stop_loss(historical_data, volatility)
                        if signal == 'BUY':
                            stop_loss = entry_price - stop_loss_value
                        else: # SELL
                            stop_loss = entry_price + stop_loss_value
                        print(f"Entering {signal} trade at {entry_price} with stop-loss at {stop_loss}")


            time.sleep(3600 * 4)  # Wait for the next 4-hour candle
        except Exception as e:
            print(f"An error occurred: {e}")
            # Re-authenticate if the session expires
            data = obj.generateSession(config.CLIENT_CODE, config.PIN, TOTP(config.TOTP_SECRET).now())
            if data and data.get('status') and data.get('data'):
                refreshToken = data['data']['refreshToken']
            else:
                print("Re-authentication failed.")


def get_historical_data(smartApi, instrument_token, timeframe):
    try:
        # Define the request parameters
        params = {
            "exchange": "NSE",
            "symboltoken": instrument_token,
            "interval": timeframe,
            "fromdate": (pd.Timestamp.now() - pd.Timedelta(days=30)).strftime('%Y-%m-%d %H:%M'),
            "todate": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')
        }
        # Fetch the historical data
        candle_data = smartApi.getCandleData(params)

        if candle_data and candle_data.get('data'):
            # Convert the data to a pandas DataFrame
            df = pd.DataFrame(candle_data['data'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            return df
        else:
            return None
    except Exception as e:
        print(f"Error fetching historical data: {e}")
        return None

if __name__ == "__main__":
    main()
