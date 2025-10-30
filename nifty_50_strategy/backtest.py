
import pandas as pd
from strategy import MeanReversionStrategy

def backtest(data, strategy):
    in_trade = False
    entry_price = 0
    stop_loss = 0
    trade_direction = None
    trades = []

    for i in range(1, len(data)):
        current_data = data.iloc[:i]
        signal = strategy.generate_signals(current_data)

        latest_candle = current_data.iloc[-1]
        current_price = latest_candle['close']
        ema = latest_candle['ema']

        if not in_trade and (signal == 'BUY' or signal == 'SELL'):
            in_trade = True
            entry_price = current_price
            trade_direction = signal
            volatility = 16  # Placeholder for volatility
            stop_loss_value = strategy.get_stop_loss(current_data, volatility)
            if signal == 'BUY':
                stop_loss = entry_price - stop_loss_value
            else: # SELL
                stop_loss = entry_price + stop_loss_value
            trades.append({'entry_price': entry_price, 'signal': signal, 'entry_date': latest_candle.name, 'stop_loss': stop_loss})

        elif in_trade:
            if strategy.get_exit_signal(current_price, ema, trade_direction):
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
    # Load historical data from a CSV file
    # Make sure to have a 'nifty_50_data.csv' file in the same directory
    try:
        data = pd.read_csv('nifty_50_strategy/nifty_50_data.csv', index_col='timestamp', parse_dates=True)
    except FileNotFoundError:
        print("Error: 'nifty_50_data.csv' not found. Please create this file with historical data.")
        return

    # Create an instance of the trading strategy
    strategy = MeanReversionStrategy()

    # Run the backtest
    trades = backtest(data, strategy)

    # Print the results
    for trade in trades:
        print(trade)

if __name__ == "__main__":
    main()
