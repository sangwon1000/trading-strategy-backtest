import pandas as pd
import pandas_ta as ta
import logging
import traceback
import numpy as np
from functions_order import execute, check_position, position_sizing, stop_loss
from stats import Stats
from strategy import MeanReversion, TrendFollowing
import os
import sys
path = os.path.dirname(__file__)
sys.path.append(os.path.join(path, '..'))
from data_engine.data_cloud import DataEngineCloud

# Generates all trades and breakout_df (ohlc data)
class Backtest(MeanReversion, TrendFollowing):
    def __init__(self,inst_id, historical_price, account_equity, fee):
        self.inst_id = inst_id
        self.historical_price = historical_price.copy()
        self.initial_equity = account_equity
        # fee should account for exhcange fee and slippage
        # is only applied to closing trades (not opening trades), fee should be set 2x higher
        self.fee = fee
        
        # trading timeframe
        # trade_timeframe = '1d'
        # if trade_timeframe == '1d':
        #     self.multiplier = 1
        # else:
        #     self.multiplier = 1
        self.multiplier = 1

        self.historical_price['open_pct'] = 0
        self.historical_price['open_pct'] = self.historical_price['open'].pct_change()
        self.historical_price['high_pct'] = 0
        self.historical_price['high_pct'] = self.historical_price['high'].pct_change()

        self.historical_price['close_pct'] = 0
        self.historical_price['close_pct'] = self.historical_price['close'].pct_change()
        self.historical_price['low_pct'] = 0
        self.historical_price['low_pct'] = self.historical_price['low'].pct_change()

        # open price start from 100 and roll perchange change
        self.historical_price['open'] = 100
        self.historical_price['open'] = self.historical_price['open'] * (1 + self.historical_price['open_pct']).cumprod()
        
        self.historical_price['high'] = 100
        self.historical_price['high'] = self.historical_price['high'] * (1 + self.historical_price['high_pct']).cumprod()
        self.historical_price['close'] = 100
        self.historical_price['close'] = self.historical_price['close'] * (1 + self.historical_price['close_pct']).cumprod()
        self.historical_price['low'] = 100
        self.historical_price['low'] = self.historical_price['low'] * (1 + self.historical_price['low_pct']).cumprod()

        self.historical_price['pct_returns'] = self.historical_price['close'].pct_change()
        self.historical_price['log_returns'] = np.log(self.historical_price['close'] / self.historical_price['close'].shift(1))

        self.std_window = 1 * 2
        self.historical_price['std_close'] = self.historical_price['close'].rolling(window=self.std_window).std() / self.historical_price['close']
        self.historical_price['std_close_pct'] = self.historical_price['std_close'].pct_change()
        self.historical_price['volume'] = self.historical_price['volume'] * self.historical_price['close'] / 1000000
        self.historical_price['turnover_m'] = self.historical_price['volume'] * self.historical_price['close'] / 1000000

        # print(self.historical_price)
        # print(self.historical_price.dtypes)
        # raise Exception
        self.atr_window = 5 * self.multiplier
        self.historical_price['atr'] = ta.atr(self.historical_price['high'], self.historical_price['low'], self.historical_price['close'], self.atr_window, mamode=None)
        self.historical_price['atrp'] = self.historical_price['atr'] / self.historical_price['close']
        # Use b1 (one bar before) to prevent look-ahead bias
        self.historical_price['atr_b1'] = self.historical_price['atr'].shift(1)
        
        
        TrendFollowing.__init__(self, account_equity, self.historical_price, self.fee, self.multiplier)
        MeanReversion.__init__(self, account_equity, self.historical_price, self.fee, self.multiplier)
        
        # list how many days condition
        self.days_since_listing = 30 * self.multiplier
        # self.start_window = min(self.atr_window, self.upper_window, self.lower_window, self.sum_window, self.days_since_listing)
        self.start_window = 5
    def backtest(self):
        for date, bar in self.historical_price.iloc[self.start_window:].iterrows():
            MeanReversion.on(self, date, bar)
            TrendFollowing.on(self, date, bar)
        
        try:
            self.all_trades = pd.concat(self.trades)
        except ValueError:
            logging.info(f"No trades made for {self.inst_id}")
            pass

        try:
            self.all_trades_tf = pd.concat(self.trades_tf)
        except ValueError:
            logging.info(f"No trades made for MR {self.inst_id}")
            pass

        
        # self.all_trades = self.all_trades[:-1]
        # print(self.all_trades)
        stats_trend_following = Stats(self.historical_price, self.all_trades, self.account_equity, self.initial_equity, self.fee, self.inst_id)
        stats_mean_reversion = Stats(self.historical_price, self.all_trades_tf, self.account_equity_tf, self.initial_equity, self.fee, self.inst_id)
        trade_stats, all_trades, daily_drawdown = stats_trend_following.calculate_stats()
        # trade_stats, all_trades, daily_drawdown = stats_mean_reversion.calculate_stats()

        # self.historical_price['Account Equity MA'] = ta.sma(self.historical_price['Account Equity'], 200 * self.multiplier)
        # self.historical_price['Account Equity TF MA'] = ta.sma(self.historical_price['Account Equity TF'], 200 * self.multiplier)
        # self.historical_price['Daily Drawdown'] = daily_drawdown
        

        
        self.historical_price['corr_mr_v_vol'] = self.historical_price['account_equity_mr'].rolling(1* self.multiplier).corr(self.historical_price['std_close_pct'])
        self.historical_price['std_tf'] = self.historical_price['account_equity_tf'].rolling(window=self.std_window).std() / self.historical_price['account_equity_tf']
        self.historical_price['std_mr'] = self.historical_price['account_equity_mr'].rolling(window=self.std_window).std() / self.historical_price['account_equity_mr']

        
        cloud = DataEngineCloud()
        cloud.update_historical_price(self.historical_price)
        self.historical_price.to_csv(f'output/{self.inst_id}_bar_data.csv')

        if all_trades is not None:
            all_trades.to_csv(f'output/{self.inst_id}_trades.csv')
        return trade_stats


# Impovements
# account fees for opening trades
# account equity change for opened trades until closing trades
        
# time series account equity and time series win rate