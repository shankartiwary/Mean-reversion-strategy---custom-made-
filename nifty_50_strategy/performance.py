
import pandas as pd
import quantstats as qs
import numpy as np

def calculate_performance_metrics(trades, price_data):
    """
    Calculates performance metrics for a backtest.
    """
    if not trades:
        return {}

    trades_df = pd.DataFrame(trades)

    # --- Calculate Win/Loss Stats & PnL ---
    trades_df['pnl'] = (trades_df['exit_price'] - trades_df['entry_price']) / trades_df['entry_price']
    trades_df.loc[trades_df['signal'] == 'SELL', 'pnl'] *= -1

    winning_trades = trades_df[trades_df['pnl'] > 0]
    losing_trades = trades_df[trades_df['pnl'] <= 0]

    win_rate = (len(winning_trades) / len(trades_df)) * 100 if len(trades_df) > 0 else 0

    # --- Calculate Expectancy ---
    avg_win = winning_trades['pnl'].mean() if not winning_trades.empty else 0
    avg_loss = losing_trades['pnl'].mean() if not losing_trades.empty else 0
    expectancy = (win_rate / 100 * avg_win) + ((1 - win_rate / 100) * abs(avg_loss))

    # --- Create a daily returns series from trades for quantstats ---
    trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date']).dt.tz_localize(None)
    trades_df['exit_date'] = pd.to_datetime(trades_df['exit_date']).dt.tz_localize(None)

    # Reindex price data to ensure it covers the full backtest period
    daily_prices = price_data['close'].resample('D').last().ffill()
    strategy_returns = pd.Series(0, index=daily_prices.index)

    for _, trade in trades_df.iterrows():
        # Simple PnL attribution to the exit day
        if pd.notna(trade['exit_date']):
             strategy_returns.loc[trade['exit_date'].date()] += trade['pnl']

    # --- Calculate quantstats metrics on strategy returns ---
    sharpe = qs.stats.sharpe(strategy_returns)
    max_drawdown = qs.stats.max_drawdown(strategy_returns)
    total_return = qs.stats.comp(strategy_returns) * 100

    return {
        "Total Return (%)": total_return,
        "Win Ratio (%)": win_rate,
        "Winning Trades": len(winning_trades),
        "Losing Trades": len(losing_trades),
        "Sharpe Ratio": sharpe,
        "Max Drawdown": max_drawdown,
        "Expectancy": expectancy if not np.isnan(expectancy) else 0
    }
