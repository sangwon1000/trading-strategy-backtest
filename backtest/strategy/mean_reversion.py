import pandas as pd
import numpy as np
from functions_order import execute, check_position, position_sizing, stop_loss

class MeanReversion:
    def __init__(self, account_equity, historical_price, fee, multiplier):
        self.historical_price = historical_price
        self.account_equity_tf = account_equity
        print(self.account_equity_tf)
        self.multiplier = multiplier
        self.fee = fee
        self.trades_tf = []
        self.all_trades_tf = None
        self.leverage = 1
        self.min_spread = 0.00
        self.sum_window = 1 * self.multiplier
        self.start_window = self.sum_window
        # self.historical_price['tree_frog_bar_return'] = self.historical_price['close'].pct_change()
        self.historical_price['tree_frog_sum_log_returns'] = self.historical_price['log_returns'].rolling(window=self.sum_window, min_periods=self.sum_window).sum()        
        self.historical_price['bet_size'] = -1 * self.historical_price['tree_frog_sum_log_returns']
        self.historical_price['account_equity_mr'] = self.account_equity_tf

    def open_long(self, date, bar):
        position='Open Long'
        if (
            # bar['std_close_pct'] < self.min_spread and 
            check_position(self.trades_tf, position) == True
            ):
            unit = (self.leverage * abs(bar['bet_size']) * self.account_equity_tf)/bar['close']
            trade = execute(date=date, position=position, price=bar['close'], unit=unit)
            self.trades_tf.append(trade)

    def open_short(self, date, bar):
        position='Open Short'
        if (
            # bar['std_close_pct'] < self.min_spread and 
            check_position(self.trades_tf, position) == True
            ):
            unit = (self.leverage * abs(bar['bet_size']) * self.account_equity_tf)/bar['close']
            trade = execute(date=date, position=position, price=bar['close'], unit=unit)
            self.trades_tf.append(trade) 
            print(unit)

    def close_long(self, date, bar):
        position='Close Long'
        if len(self.trades_tf) > 0 and date != self.trades_tf[-1].loc[0, 'Trade Date']:
            if self.trades_tf[-1].loc[0, 'Position'] == 'Open Long':
                price = bar['close']
                unit = self.trades_tf[-1].loc[0, 'Unit']
                trade = execute(date=date, position=position, price=price, unit=unit)
                self.trades_tf.append(trade)
                # # pnl has to be calculated here (not in Stats), as it has to update account_equity before next trade for right position sizing
                pnl = unit * (price - self.trades_tf[-2].loc[0, 'Fill Price']) - (unit * price * self.fee)
                self.account_equity_tf += pnl
                self.open_long(date, bar)
                self.open_short(date, bar)

    def close_short(self, date, bar):
        position='Close Short'
        if len(self.trades_tf) > 0 and date != self.trades_tf[-1].loc[0, 'Trade Date']:
            if self.trades_tf[-1].loc[0, 'Position'] == 'Open Short':
                price = bar['close']
                unit = self.trades_tf[-1].loc[0, 'Unit']
                trade = execute(date=date, position=position, price=price, unit=unit)
                self.trades_tf.append(trade)
                # # pnl has to be calculated here (not in Stats), as it has to update account_equity before next trade for right position sizing
                pnl = unit * (self.trades_tf[-2].loc[0, 'Fill Price'] - price) - (unit * price * self.fee)
                self.account_equity_tf += pnl
                self.open_long(date, bar)
                self.open_short(date, bar)
        
    def on(self, date, bar):
        # limitation: close all position and switch, not able to handle dynamically adding or reducing position
        # date_str, time_str = str(date).split()
        # if time_str == '00:00:00':
        self.open_long(date, bar)
        self.close_long(date, bar)
        self.open_short(date, bar)
        self.close_short(date, bar)
        
        self.historical_price.at[date,'account_equity_mr'] = self.account_equity_tf