
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
        data['ema'] = ta.ema(data['close'], length=self.ema_period)
        data['rsi'] = ta.rsi(data['close'], length=self.rsi_period)
        keltner = ta.kc(data['high'], data['low'], data['close'], length=self.keltner_period, scalar=self.keltner_multiplier, mamode='ema')
        if keltner is not None and not keltner.empty:
            data = data.join(keltner)
        data['std_dev'] = data['close'].rolling(window=self.std_dev_period).std()
        data['upper_std_dev'] = data['ema'] + self.std_dev_multiplier * data['std_dev']
        data['lower_std_dev'] = data['ema'] - self.std_dev_multiplier * data['std_dev']
        data['z_score'] = (data['close'] - data['close'].rolling(window=self.z_score_period).mean()) / data['close'].rolling(window=self.z_score_period).std()
        data['atr'] = ta.atr(data['high'], data['low'], data['close'], length=self.atr_period)
        return data

    def generate_signals(self, data):
        # This function now returns the latest signal from a pre-calculated frame
        if 'signal' not in data.columns:
            data = self.calculate_all_signals(data)

        if not data.empty:
            return data['signal'].iloc[-1]
        return 'HOLD'

    def calculate_all_signals(self, data):
        data = self.calculate_indicators(data)

        # Conditions for buy and sell signals
        buy_conditions = (
            (data['z_score'] < -2) &
            (data['rsi'] < self.rsi_oversold) &
            (data['close'] < data[f'KCLe_{self.keltner_period}_{self.keltner_multiplier}']) &
            (data['close'] < data['lower_std_dev'])
        )
        sell_conditions = (
            (data['z_score'] > 2) &
            (data['rsi'] > self.rsi_overbought) &
            (data['close'] > data[f'KCUe_{self.keltner_period}_{self.keltner_multiplier}']) &
            (data['close'] > data['upper_std_dev'])
        )

        # Generate signals
        data['signal'] = 'HOLD'
        data.loc[buy_conditions, 'signal'] = 'BUY'
        data.loc[sell_conditions, 'signal'] = 'SELL'

        return data

    def get_stop_loss(self, atr_value, volatility):
        if volatility < 15:
            return 1.5 * atr_value
        elif 15 <= volatility <= 18:
            return 1.75 * atr_value
        else:
            return 2 * atr_value

    def get_exit_signal(self, current_price, ema, trade_direction):
        if trade_direction == 'BUY' and current_price >= ema:
            return True
        elif trade_direction == 'SELL' and current_price <= ema:
            return True
        return False
