from functions_order import execute, check_open_position, check_position, position_sizing, stop_loss

class TrendFollowing:
    def __init__(self, account_equity, historical_price, fee, multiplier):
        self.fee = fee
        self.multiplier = multiplier
        self.historical_price = historical_price
        self.long_breakout = True
        self.short_breakout = False 
        self.account_equity = account_equity
        self.account_equity_short = account_equity
        self.trades = []
        self.all_trades = None

        self.upper_window = 1 * self.multiplier
        self.lower_window = 14 * self.multiplier       
        # all time high
        # self.historical_price['long_upper_bound'] = self.historical_price['high'].cummax().shift(1)
        self.historical_price['long_upper_bound'] = self.historical_price['high'].rolling(window=self.upper_window, min_periods=1).max().shift(1).iloc[self.upper_window:]
        self.historical_price['long_lower_bound'] = self.historical_price['low'].rolling(window=self.lower_window, min_periods=1).min().shift(1).iloc[self.lower_window:]
        # self.historical_price['long_stop_loss'] = self.historical_price['long_upper_bound']-(self.historical_price['atr_b1']*self.atr_multiplier)
        self.historical_price['long_stop_loss'] = self.historical_price['long_lower_bound']
        
        self.upper_window = 50 * self.multiplier
        self.lower_window = 25 * self.multiplier
        # self.historical_price['short_lower_bound'] = self.historical_price['low'].cummin().shift(1)
        self.historical_price['short_lower_bound'] = self.historical_price['low'].rolling(window=self.upper_window, min_periods=1).min().shift(1).iloc[self.upper_window:]
        self.historical_price['short_upper_bound'] = self.historical_price['high'].rolling(window=self.lower_window, min_periods=1).max().shift(1).iloc[self.lower_window:]
        # self.historical_price['short_stop_loss'] = self.historical_price['short_lower_bound']+(self.historical_price['atr_b1']*self.atr_multiplier)
        self.historical_price['short_stop_loss'] = self.historical_price['short_upper_bound']
    
        self.historical_price['account_equity_tf'] = self.account_equity
        self.historical_price['account_equity_tf_short'] = self.account_equity

    def on(self, date, bar):
        if self.long_breakout == True:
        # equity curve
            if check_open_position(self.trades) == True:
                pnl = self.account_equity * self.historical_price.at[date,'pct_returns']
                self.account_equity += pnl
                self.historical_price.at[date,'account_equity_tf'] = self.account_equity
                # print(self.account_equity)
                # print((self.account_equity * self.historical_price.at[date,'pct_returns']))
            else:
                self.historical_price.at[date,'account_equity_tf'] = self.account_equity

            position='Open Long'
            if (
                bar['high'] > bar['long_upper_bound']
                and check_position(self.trades, position) == True
                and bar['tree_frog_sum_log_returns'] > 0
                ):
                unit = position_sizing(self.account_equity, 0.01, bar['atr_b1'], bar['long_upper_bound'])
                
                trade = execute(date=date, position=position, price=bar['long_upper_bound'], unit=unit)
                self.trades.append(trade)
                
            # if i/o elif is conservative approach as it assumes intra-bar high/low can be made in any given time
            # using elif would be more aggresive approach, as it will move to next bar for TP/SL
            position='Close Long'
            import pandas as pd
            import numpy as np
            if check_position(self.trades, position) == True:
                if  (
                    ((bar['low'] < bar['long_lower_bound'])
                    )
                    # or (date == self.trades[-1].loc[0, 'Trade Date']+ pd.DateOffset(1) and bar['pct_returns'] < 0)
                    and check_position(self.trades, position) == True
                    ):
                    # if date == self.trades[-1].loc[0, 'Trade Date']+ pd.DateOffset(1):
                    #     price = bar['close']
                    # else:
                    price = bar['long_lower_bound']
                    # if (
                        
                    #     ):
                    #     print(self.trades[-1].loc[0, 'Trade Date'])
                    #     print()
                    #     print(type(self.trades[-1].loc[0, 'Trade Date']))
                    #     raise Exception
                        
                    unit = self.trades[-1].loc[0, 'Unit']

                    # try:
                    #     unit = self.trades[-1].loc[0, 'Unit']
                    # except:
                    #     unit = 0
                    trade = execute(date=date, position=position, price=price, unit=unit)
                    self.trades.append(trade)
                    # pnl has to be calculated here (not in Stats), as it has to update account_equity before next trade for right position sizing
                    
                    # pnl = unit * (price - self.trades[-2].loc[0, 'Fill Price']) - (unit * price * self.fee)
                    # self.account_equity += pnl
                    
                # self.historical_price.at[date,'account_equity_tf'] = self.account_equity
            


        if self.short_breakout == True:
            position ='Open Short'
            if (
                bar['low'] < bar['short_lower_bound']
                and check_position(self.trades, position) == True
            ):
                unit = position_sizing(self.account_equity, 0.01, bar['atr_b1'], bar['short_lower_bound'])
                trade = execute(date=date, position=position, price=bar['short_lower_bound'], unit=unit)
                self.trades.append(trade)

            position='Close Short'
            if  (
                (bar['high'] > stop_loss(self.trades, position, self.historical_price) or bar['high'] > bar['short_upper_bound'])
                and check_position(self.trades, position) == True
                ):

                price = min(stop_loss(self.trades, position, self.historical_price), bar['short_upper_bound'])
                unit = self.trades[-1].loc[0, 'Unit']
                # try:
                #     unit = self.trades[-1].loc[0, 'Unit']
                # except:
                #     unit = 0
                trade = execute(date=date, position=position, price=price, unit=unit)
                self.trades.append(trade)

                pnl = unit * (self.trades[-2].loc[0, 'Fill Price'] - price) - (unit * price * self.fee)
                self.account_equity_short += pnl

            self.historical_price.at[date,'account_equity_tf_short'] = self.account_equity_short
        
        

        