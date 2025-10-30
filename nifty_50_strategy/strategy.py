
import pandas as pd
import pandas_ta as ta
import numpy as np

class MeanReversionStrategy:
    def __init__(self, ema_period=20, rsi_period=14, rsi_overbought=80, rsi_oversold=20, atr_period=14, std_dev_period=14, std_dev_multiplier=2.5, z_score_period=14):
        self.ema_period = ema_period
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.atr_period = atr_period
        self.std_dev_period = std_dev_period
        self.std_dev_multiplier = std_dev_multiplier
        self.z_score_period = z_score_period

    def calculate_indicators(self, data):
        """Calculates all technical indicators for the backtest."""
        data['log_price'] = np.log(data['close'])

        # Calculate EMA on both close and log prices
        data['ema'] = ta.ema(data['close'], length=self.ema_period)
        data['ema_log'] = ta.ema(data['log_price'], length=self.ema_period)

        # Calculate RSI on log prices
        data['rsi'] = ta.rsi(data['log_price'], length=self.rsi_period)

        # --- Corrected Standard Deviation Calculation (in Log Space) ---
        log_std_dev = data['log_price'].rolling(window=self.std_dev_period).std()
        data['upper_std_dev_log'] = data['ema_log'] + self.std_dev_multiplier * log_std_dev
        data['lower_std_dev_log'] = data['ema_log'] - self.std_dev_multiplier * log_std_dev

        # Calculate Z-score on log prices
        log_mean = data['log_price'].rolling(window=self.z_score_period).mean()
        data['z_score'] = (data['log_price'] - log_mean) / log_std_dev

        # Calculate ATR on regular prices
        data['atr'] = ta.atr(data['high'], data['low'], data['close'], length=self.atr_period)

        return data

    def generate_signals(self, data, indicators=['rsi', 'z_score', 'std_dev']):
        if 'signal' not in data.columns:
            data = self.calculate_all_signals(data, indicators)

        if not data.empty:
            return data['signal'].iloc[-1]
        return 'HOLD'

    def calculate_all_signals(self, data, indicators=['rsi', 'z_score', 'std_dev']):
        """Calculates the 'signal' column for the entire dataframe based on flexible logic."""
        data = self.calculate_indicators(data)

        buy_conditions = []
        sell_conditions = []

        if 'rsi' in indicators:
            # Ensure RSI is within the valid 0-100 range before applying conditions
            buy_conditions.append((data['rsi'] < self.rsi_oversold) & (data['rsi'] > 0))
            sell_conditions.append((data['rsi'] > self.rsi_overbought) & (data['rsi'] < 100))
        if 'z_score' in indicators:
            buy_conditions.append(data['z_score'] < -2)
            sell_conditions.append(data['z_score'] > 2)
        if 'std_dev' in indicators:
            buy_conditions.append(data['log_price'] < data['lower_std_dev_log'])
            sell_conditions.append(data['log_price'] > data['upper_std_dev_log'])

        if not buy_conditions:
            data['signal'] = 'HOLD'
            return data

        # Sum of conditions met for each row (True=1, False=0)
        buy_cond_sum = sum(c.astype(int) for c in buy_conditions)
        sell_cond_sum = sum(c.astype(int) for c in sell_conditions)

        # Determine the required number of conditions based on the number of selected indicators
        num_indicators = len(indicators)
        if num_indicators == 1:
            required_conditions = 1
        elif num_indicators == 2:
            required_conditions = 2
        else:  # This handles the case for 3 indicators, requiring any 2 to be met.
            required_conditions = 2

        # Generate signals based on the dynamic required conditions
        buy_signal_series = buy_cond_sum >= required_conditions
        sell_signal_series = sell_cond_sum >= required_conditions

        # Refined signal generation with np.select to handle simultaneous signals
        conditions = [
            (buy_signal_series) & (~sell_signal_series),  # Buy signal only
            (sell_signal_series) & (~buy_signal_series), # Sell signal only
        ]
        choices = ['BUY', 'SELL']
        data['signal'] = np.select(conditions, choices, default='HOLD')

        return data

    def get_stop_loss(self, atr_value, volatility):
        if volatility < 15:
            return 1.5 * atr_value
        elif 15 <= volatility <= 18:
            return 1.75 * atr_value
        else:
            return 2 * atr_value

    def get_exit_signal(self, current_price, ema, trade_direction, z_score):
        # Profit taking when z-score is 0
        if z_score is not None and abs(z_score) < 0.1: # Using a small threshold around 0
            return True
        # Original exit condition
        if trade_direction == 'BUY' and current_price >= ema:
            return True
        elif trade_direction == 'SELL' and current_price <= ema:
            return True
        return False
