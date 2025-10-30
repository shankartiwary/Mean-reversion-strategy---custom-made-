
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

    def calculate_indicators(self, data):
        # Calculate EMA
        data['ema'] = ta.ema(data['close'], length=self.ema_period)

        # Calculate RSI
        data['rsi'] = ta.rsi(data['close'], length=self.rsi_period)

        # Calculate Keltner Channels
        keltner = ta.kc(data['high'], data['low'], data['close'], length=self.keltner_period, scalar=self.keltner_multiplier, mamode='ema')
        if keltner is not None and not keltner.empty:
            data = data.join(keltner)

        # Calculate Standard Deviation
        data['std_dev'] = data['close'].rolling(window=self.std_dev_period).std()
        data['upper_std_dev'] = data['ema'] + self.std_dev_multiplier * data['std_dev']
        data['lower_std_dev'] = data['ema'] - self.std_dev_multiplier * data['std_dev']

        # Calculate Z-score
        data['z_score'] = (data['close'] - data['close'].rolling(window=self.z_score_period).mean()) / data['close'].rolling(window=self.z_score_period).std()

        # Calculate ATR
        data['atr'] = ta.atr(data['high'], data['low'], data['close'], length=self.atr_period)

        return data

    def generate_signals(self, data):
        data = self.calculate_indicators(data)

        required_columns = [
            'z_score', 'rsi', f'KCUe_{self.keltner_period}_{self.keltner_multiplier}',
            f'KCLe_{self.keltner_period}_{self.keltner_multiplier}', 'lower_std_dev', 'upper_std_dev'
        ]

        if not all(col in data.columns for col in required_columns) or data.iloc[-1][required_columns].isnull().any():
            return 'HOLD'

        latest_data = data.iloc[-1]

        # Buy signals
        buy_signal = (
            latest_data['z_score'] < -2 and
            latest_data['rsi'] < self.rsi_oversold and
            latest_data['close'] < latest_data[f'KCLe_{self.keltner_period}_{self.keltner_multiplier}'] and
            latest_data['close'] < latest_data['lower_std_dev']
        )

        # Sell signals
        sell_signal = (
            latest_data['z_score'] > 2 and
            latest_data['rsi'] > self.rsi_overbought and
            latest_data['close'] > latest_data[f'KCUe_{self.keltner_period}_{self.keltner_multiplier}'] and
            latest_data['close'] > latest_data['upper_std_dev']
        )

        if buy_signal:
            return 'BUY'
        elif sell_signal:
            return 'SELL'
        else:
            return 'HOLD'

    def get_stop_loss(self, data, volatility):
        latest_atr = data['atr'].iloc[-1]
        if volatility < 15:
            return 1.5 * latest_atr
        elif 15 <= volatility <= 18:
            return 1.75 * latest_atr
        else:
            return 2 * latest_atr

    def get_exit_signal(self, current_price, ema, trade_direction):
        if trade_direction == 'BUY' and current_price >= ema:
            return True
        elif trade_direction == 'SELL' and current_price <= ema:
            return True
        return False
