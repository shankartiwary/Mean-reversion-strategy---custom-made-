
import time
import threading
from SmartApi import SmartConnect
from pyotp import TOTP
import queue
from datetime import date, timedelta
from nsepy import get_history

from strategy import MeanReversionStrategy
import pandas as pd

class TradingBot:
    def __init__(self, log_queue):
        self.strategy = MeanReversionStrategy()
        self.log_queue = log_queue
        self.running = False
        self.thread = None
        self.smart_api = None

    def log(self, message):
        self.log_queue.put(message)

    def get_live_volatility(self):
        try:
            today = date.today()
            vix_data = get_history(symbol="INDIAVIX", start=today - timedelta(days=5), end=today, index=True)
            if not vix_data.empty:
                return vix_data['Close'].iloc[-1]
        except Exception as e:
            self.log(f"Error fetching VIX data: {e}")
        return 16  # Fallback to a default value

    def start_trading(self, api_key, api_secret, client_code, pin, totp_secret):
        if self.running:
            self.log("Bot is already running.")
            return

        self.log("Starting trading bot...")
        self.running = True

        # Authenticate with SmartAPI
        self.smart_api = SmartConnect(api_key=api_key)
        try:
            data = self.smart_api.generateSession(client_code, pin, TOTP(totp_secret).now())
            if not data or data.get('status') is False or not data.get('data'):
                self.log(f"Authentication failed: {data}")
                self.running = False
                return
            self.log("Authentication successful.")
        except Exception as e:
            self.log(f"Authentication error: {e}")
            self.running = False
            return

        self.thread = threading.Thread(target=self._trading_loop)
        self.thread.start()
        self.log("Trading bot started.")

    def stop_trading(self):
        if not self.running:
            self.log("Bot is not running.")
            return

        self.log("Stopping trading bot...")
        self.running = False
        if self.thread:
            self.thread.join()
        self.log("Trading bot stopped.")

    def _trading_loop(self):
        instrument_token = "99926000"  # NIFTY 50 index token
        timeframe = "ONE_DAY"

        in_trade = False
        entry_price = 0
        stop_loss = 0
        trade_direction = None

        while self.running:
            try:
                historical_data = self._get_historical_data(instrument_token, timeframe)
                if historical_data is not None and not historical_data.empty:
                    signal = self.strategy.generate_signals(historical_data)
                    self.log(f"Signal: {signal}")

                    latest_data = historical_data.iloc[-1]
                    current_price = latest_data['close']
                    ema = latest_data['ema']
                    z_score = latest_data.get('z_score')

                    if in_trade:
                        if self.strategy.get_exit_signal(current_price, ema, trade_direction, z_score):
                            self.log(f"Exit signal at {current_price}. Exiting trade.")
                            in_trade = False
                            trade_direction = None
                        elif (trade_direction == 'BUY' and current_price <= stop_loss) or \
                             (trade_direction == 'SELL' and current_price >= stop_loss):
                            self.log(f"Stop-loss at {current_price}. Exiting trade.")
                            in_trade = False
                            trade_direction = None

                    if not in_trade and (signal == 'BUY' or signal == 'SELL'):
                        in_trade = True
                        entry_price = current_price
                        trade_direction = signal
                        volatility = self.get_live_volatility()
                        atr_value = historical_data['atr'].iloc[-1]
                        stop_loss_value = self.strategy.get_stop_loss(atr_value, volatility)
                        if signal == 'BUY':
                            stop_loss = entry_price - stop_loss_value
                        else:
                            stop_loss = entry_price + stop_loss_value
                        self.log(f"Entering {signal} trade at {entry_price} with stop-loss at {stop_loss}")

                # Sleep for 24 hours. A daily strategy only needs to run once per day.
                time.sleep(60 * 60 * 24)
            except Exception as e:
                self.log(f"An error occurred in trading loop: {e}")
                time.sleep(60 * 60 * 24)

    def _get_historical_data(self, instrument_token, timeframe):
        try:
            params = {
                "exchange": "NSE", "symboltoken": instrument_token, "interval": timeframe,
                "fromdate": (pd.Timestamp.now() - pd.Timedelta(days=30)).strftime('%Y-%m-%d %H:%M'),
                "todate": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')
            }
            candle_data = self.smart_api.getCandleData(params)

            if candle_data and candle_data.get('data'):
                df = pd.DataFrame(candle_data['data'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                return df
            return None
        except Exception as e:
            self.log(f"Error fetching historical data: {e}")
            return None
