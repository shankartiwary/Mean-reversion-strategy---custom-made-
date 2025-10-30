
import pandas as pd
from strategy import MeanReversionStrategy

def backtest(data, strategy, volatility_data=None, indicators=['rsi', 'z_score', 'std_dev']):
    # Pre-calculate all signals
    data = strategy.calculate_all_signals(data, indicators)

    in_trade = False
    entry_price = 0
    stop_loss = 0
    trade_direction = None
    trades = []

    for i in range(1, len(data)):
        latest_candle = data.iloc[i]
        signal = latest_candle['signal']

        current_price = latest_candle['close']
        ema = latest_candle['ema']
        z_score = latest_candle.get('z_score')

        if not in_trade and (signal == 'BUY' or signal == 'SELL'):
            in_trade = True
            entry_price = current_price
            trade_direction = signal

            volatility = 16  # Default value
            if volatility_data is not None:
                # Align volatility data with the current candle's date
                date_key = latest_candle.name.date()
                if date_key in volatility_data.index:
                    volatility = volatility_data.loc[date_key]

            atr_value = latest_candle['atr']
            stop_loss_value = strategy.get_stop_loss(atr_value, volatility)

            if signal == 'BUY':
                stop_loss = entry_price - stop_loss_value
            else: # SELL
                stop_loss = entry_price + stop_loss_value
            trades.append({'entry_price': entry_price, 'signal': signal, 'entry_date': latest_candle.name, 'stop_loss': stop_loss})

        elif in_trade:
            if strategy.get_exit_signal(current_price, ema, trade_direction, z_score):
                trades[-1]['exit_price'] = current_price
                trades[-1]['exit_date'] = latest_candle.name
                in_trade = False
                trade_direction = None
            elif (trade_direction == 'BUY' and current_price <= stop_loss) or \
                 (trade_direction == 'SELL' and current_price >= stop_loss):
                trades[-1]['exit_price'] = current_price
                trades[-1]['exit_date'] = latest_candle.name
                in_trade = False
                trade_direction = None

    return trades

def main():
    # Example usage for standalone backtesting
    try:
        data = pd.read_csv('nifty_50_strategy/nifty_50_data.csv', index_col='timestamp', parse_dates=True)
    except FileNotFoundError:
        print("Error: 'nifty_50_data.csv' not found. Please create this file for standalone testing.")
        return

    strategy = MeanReversionStrategy()
    trades = backtest(data, strategy)
    print("Backtest Results:")
    for trade in trades:
        print(trade)

if __name__ == "__main__":
    main()
