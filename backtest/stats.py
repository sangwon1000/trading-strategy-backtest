import pandas as pd
import numpy as np
import logging

class Stats:
    def __init__(self, historical_price, all_trades, account_equity, initial_equity, fee, inst_id):
        self.historical_price = historical_price
        self.all_trades = all_trades.copy()
        self.account_equity = account_equity
        self.initial_equity = initial_equity
        self.fee = fee
        self.inst_id = inst_id

    def calculate_stats(self):
        if self.all_trades is not None:
            # Delete last trade if it is open position
            if self.all_trades.iloc[-1]['Position'] == 'Open Long' or self.all_trades.iloc[-1]['Position'] == 'Open Short':
                self.all_trades = self.all_trades.iloc[:-1]
            
            # backfill empty account equity
            self.historical_price['account_equity_mr'] = self.historical_price['account_equity_mr'].ffill()
            
            ###################################################################
            ############################## Stats ##############################
            ###################################################################

            self.all_trades['Trade Notional'] = self.all_trades['Fill Price'] * self.all_trades['Unit']
            self.all_trades['account_equity_mr'] = self.all_trades['Trade Date'].map(self.historical_price['account_equity_mr'])

            # Calculate P&L seperately using trades to compare with breakout_df
            # Calculate P&L for Long Trades
            # print(self.all_trades[-1])
            def locate_position(x, y):
                result = self.all_trades.loc[self.all_trades['Position'] == x, y]
                return result
            



            close_long_unit = locate_position('Close Long', 'Unit')
            close_long_fill_price = locate_position('Close Long', 'Fill Price')
            open_long_unit = locate_position('Open Long', 'Unit')
            open_long_fill_price = locate_position('Open Long', 'Fill Price')
            
            self.all_trades.loc[self.all_trades['Position'] == 'Close Long', 'P&L'] = open_long_unit * (close_long_fill_price.values - open_long_fill_price.values) - (open_long_unit * close_long_fill_price.values * self.fee)
            
            # Calculate P&L for Short Trades
            self.all_trades.loc[self.all_trades['Position'] == 'Close Short', 'P&L'] = self.all_trades.loc[self.all_trades['Position'] == 'Open Short', 'Unit'] * (self.all_trades.loc[self.all_trades['Position'] == 'Open Short', 'Fill Price'].values - self.all_trades.loc[self.all_trades['Position'] == 'Close Short', 'Fill Price'].values) - self.all_trades.loc[self.all_trades['Position'] == 'Open Short', 'Unit'] * self.all_trades.loc[self.all_trades['Position'] == 'Close Short', 'Fill Price'].values * self.fee
            
            # Calculate P&L Percentage and Flag
            self.all_trades['P&L Percentage'] = (self.all_trades['account_equity_mr']/self.all_trades['account_equity_mr'].shift(1))-1
            self.all_trades['P&L Percentage'] = self.all_trades['P&L Percentage'].replace(0, np.nan)
            self.all_trades['Flag'] = self.all_trades.apply(lambda x: 'Win' if x['P&L'] > 0 else ('Lose' if x['P&L'] < 0 else np.nan), axis = 1)

            win_trade_count = (self.all_trades['P&L'] > 0).sum()
            lose_trade_count = (self.all_trades['P&L'] < 0).sum()
            win_rate = win_trade_count/(win_trade_count+lose_trade_count)
            gross_profit = self.all_trades.loc[self.all_trades['P&L'] > 0, 'P&L'].sum()
            gross_loss = self.all_trades.loc[self.all_trades['P&L'] < 0, 'P&L'].sum()
            pnl_sum = self.all_trades['P&L'].sum()

            # DD
            roll_max = self.historical_price['account_equity_mr'].cummax()
            self.historical_price['Daily Drawdown'] = daily_drawdown = self.historical_price['account_equity_mr']/roll_max - 1.0
            max_daily_drawdown = daily_drawdown.cummin().min()
            
            if gross_loss != 0:
                profit_factor = abs(gross_profit/gross_loss)
            else:
                profit_factor = 0

            logging.info(f"Buy and Hold Return        : {round((self.historical_price['close'].iloc[-1] - self.historical_price['close'].iloc[0])/self.historical_price['close'].iloc[0] * 100, 2)}%")
            logging.info("*********************************************")
            logging.info("*               Trade Statistics            *")
            logging.info("*********************************************")
            logging.info(f"# Number of bars           : {len(self.historical_price)}")
            logging.info(f"# Number of trades         : {len(self.all_trades)/2}")
            logging.info(f"# Number of positive P&L   : {win_trade_count}")
            logging.info(f"# Number of negative P&L   : {lose_trade_count}")
            logging.info(f"% Win Rate                 : {str(round(win_rate*100,2))}%")
            logging.info(f"# Profit Factor            : {round(profit_factor,2)}")
            logging.info(f"% Return                   : {str(round((self.account_equity - self.initial_equity)/self.initial_equity * 100,2))}%")
            ### temporary fix, why is account equity less than 0?
            if self.account_equity < 0:
                self.account_equity = 0
            ###
            logging.info(f"% CAGR                     : {round((((self.account_equity/self.initial_equity)**(1/((len(self.historical_price)/24)/365)))-1)*100,2)}%")
            logging.info(f"$ Initial Equity           : {self.initial_equity}")
            logging.info(f"$ P&L                      : {round(pnl_sum,2)}")
            logging.info(f"$ Final Account Equity     : {round(self.account_equity,2)}")
            logging.info("")
            logging.info("*********************************************")
            logging.info("*                   Risk                    *")
            logging.info("*********************************************")

            logging.info(f"% Max Drawdown             : {round(max_daily_drawdown*100,2)}%")
            logging.info(f"% ATRP Mean                : {self.historical_price['atrp'].mean()}")
            logging.info(f"% ATRP Median              : {self.historical_price['atrp'].median()}")
            logging.info(f"% ATRP Maximum             : {self.historical_price['atrp'].max()}")
            logging.info(f"% ATRP Minimum             : {self.historical_price['atrp'].min()}")
            # logging.info(f"~ Max Drawdown Period      : {self.historical_price['Account Equity'].idxmax()} ~ {self.historical_price.loc[self.historical_price['Account Equity'].idxmax():]['Account Equity'].idxmin()}")
            # logging.info(f"# Max Drawdown Duration    : {len(self.historical_price.loc[self.historical_price['Account Equity'].idxmax():self.historical_price.loc[self.historical_price['Account Equity'].idxmax():]['Account Equity'].idxmin()])} bars")
            # logging.info(f"/ Risk Reward Ratio        : {1}")

            # make dataframe for stats
            stat_map = {
                'Number of bars' : [len(self.historical_price)],
                'Number of trades' : [len(self.all_trades)/2],
                'Number of positive P&L' : [win_trade_count],
                'Number of negative P&L' : [lose_trade_count],
                'Win Rate' : [win_rate],
                'Buy and Hold Return' : [((self.historical_price['close'].iloc[-1] - self.historical_price['close'].iloc[0])/self.historical_price['close'].iloc[0])],
                'Profit Factor' : [profit_factor],
                
                'Return' : [(self.account_equity - self.initial_equity)/self.initial_equity],
                'CAGR' : [(((self.account_equity/self.initial_equity)**(1/((len(self.historical_price)/24)/365)))-1)],
                'Initial Equity' : [self.initial_equity],
                'P&L' : [pnl_sum],
                'Final Account Equity' : [self.account_equity],
                'Max Drawdown' : [max_daily_drawdown],
                'ATRP Mean' : [self.historical_price['atrp'].mean()],
                'ATRP Median' : [self.historical_price['atrp'].median()],
                'ATRP Maximum' : [self.historical_price['atrp'].max()],
                'ATRP Minimum' : [self.historical_price['atrp'].min()],
            }

            stats = pd.DataFrame(data=stat_map)
        
            # Sanity check: compare breakout_df with all_trades
            if round(self.historical_price['account_equity_tf'].iloc[-1], 10) == round(self.all_trades['P&L'].sum() + self.initial_equity, 10):
                logging.info("Account Equity Matches")
            else:
                logging.info("Account Equity does not match")
                logging.info(f"Account Equity in breakout_df:{self.historical_price['account_equity_tf'].iloc[-1]}")
                logging.info(f"Account Equity in all_trades :{self.all_trades['P&L'].sum() + self.initial_equity}" )
            
            
            return stats, self.all_trades, self.historical_price['Daily Drawdown']
        else:
            return None, None
