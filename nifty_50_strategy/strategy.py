
import pandas as pd
import pandas_ta as ta
import numpy as np

class MeanReversionStrategy:
    def __init__(self, ema_period=20, rsi_period=14, rsi_overbought=75, rsi_oversold=25, keltner_period=20, keltner_multiplier=2, atr_period=14, std_dev_period=20, std_dev_multiplier=2.5, z_score_period=20):
        self.ema_period = ema_period
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.keltner_period = keltner_period
        self.keltner_multiplier = keltner_multiplier
        self.atr_period = atr_period
        self.std_dev_period = std_dev_period
        self.std_dev_multiplier = std_dev_multiplier
        self.z_score_period = z_score_period

    def _get_log_prices(self, data):
        """Calculates 21-day logarithmic prices."""
        return np.log(data['close'].tail(21))

    def calculate_indicators(self, data):
        log_prices = self._get_log_prices(data)

        # Calculate EMA
        data['ema'] = ta.ema(data['close'], length=self.ema_period)

        # Calculate RSI on log prices
        data['rsi'] = ta.rsi(log_prices, length=self.rsi_period).iloc[-1] if len(log_prices) >= self.rsi_period else np.nan

        # Calculate Standard Deviation on log prices
        log_std_dev = log_prices.rolling(window=self.std_dev_period).std().iloc[-1]
        data['upper_std_dev'] = data['ema'] + self.std_dev_multiplier * log_std_dev
        data['lower_std_dev'] = data['ema'] - self.std_dev_multiplier * log_std_dev

        # Calculate Z-score on log prices
        log_mean = log_prices.rolling(window=self.z_score_period).mean().iloc[-1]
        data['z_score'] = (log_prices.iloc[-1] - log_mean) / log_std_dev if log_std_dev > 0 else 0

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
        data = self.calculate_indicators(data)

        buy_conditions = []
        sell_conditions = []

        if 'rsi' in indicators:
            buy_conditions.append(data['rsi'] < self.rsi_oversold)
            sell_conditions.append(data['rsi'] > self.rsi_overbought)
        if 'z_score' in indicators:
            buy_conditions.append(data['z_score'] < -2)
            sell_conditions.append(data['z_score'] > 2)
        if 'std_dev' in indicators:
            buy_conditions.append(data['close'] < data['lower_std_dev'])
            sell_conditions.append(data['close'] > data['upper_std_dev'])

        # Trigger if at least two conditions are met
        buy_signal = sum(buy_conditions) >= 2
        sell_signal = sum(sell_conditions) >= 2

        data['signal'] = 'HOLD'
        if buy_signal:
            data.loc[data.index[-1], 'signal'] = 'BUY'
        elif sell_signal:
            data.loc[data.index[-1], 'signal'] = 'SELL'

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
