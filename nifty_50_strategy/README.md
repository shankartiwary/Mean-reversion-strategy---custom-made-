
# Nifty 50 Mean Reversion Trading Bot

This project is a Streamlit-based web application for a mean reversion trading strategy for the Nifty 50 index. The strategy uses a combination of Z-score, RSI, Keltner Channels, and Standard Deviation to generate trading signals.

## Features

- **Live Trading:** Connect to the Angel One Smart API to run the trading bot in real-time.
- **Backtesting:** Upload historical data in CSV format to test the trading strategy's performance.
- **Interactive UI:** A user-friendly web interface built with Streamlit to control the bot and view its activity.

## Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd nifty-50-strategy
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Application

To run the Streamlit application, use the following command:

```bash
streamlit run app.py
```

### Live Trading

1.  Navigate to the "Live Trading" mode in the sidebar.
2.  Enter your Angel One API credentials.
3.  Click the "Start Bot" button to begin trading.
4.  Monitor the bot's activity in the logs.

### Backtesting

1.  Navigate to the "Backtesting" mode in the sidebar.
2.  Upload a CSV file with historical data. The CSV should have the following columns: `timestamp`, `open`, `high`, `low`, `close`, `volume`.
3.  Click the "Run Backtest" button to see the results.
