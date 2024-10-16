## Description

This is my old project for backtesting trading strategies and visualizing backtest analytics for crypto pairs. There are two strategies used in this project;
- Trend following strategy - simplified version of The Turtle Trading breakout strategy without pyramiding.
- Mean reversion strategy - Daily Weekly Variance Differential Strategy introduced by David Kim, aka Quant Daddy.

## Workflow

- data_engine/main.py gets spot tickers available for trading on OKX exchange and updates price data in local Sqlite database
- backtest/main.py runs the backtest and outputs trade statistics (backtest/stats.py)
- backtest/main.py notifies completion or failure of the code to my Telegram account, and updates Supabase cloud SQL storage
- Plotly is used for visualization of trade statistics locally, Grafana for visualization on cloud.

## References:

Turtle Strategy: https://oxfordstrat.com/coasdfASD32/uploads/2016/01/turtle-rules.pdf

Daily Weekly Variance Differential: https://brunch.co.kr/@quantdaddy/160#:~:text=%EC%9D%BC%EA%B0%84%2D%EC%A3%BC%EA%B0%84%20%EB%B6%84%EC%82%B0%EC%B0%A8%20%EC%A0%84%EB%9E%B5(Daily%2DWeekly%20Variance%20Differential,Variance)%EA%B3%BC%20%EC%A3%BC%EA%B0%84%20%EB%B6%84%EC%82%B0(Weekly

