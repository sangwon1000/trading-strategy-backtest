import logging
from backtesting_ngine import Backtest
import concurrent.futures
import pandas as pd
import os
import sys
path = os.path.dirname(__file__)
sys.path.append(os.path.join(path, '..'))
from data_engine.data_local import DataEngine
from telegram.message import send_success_message, send_fail_message
# import traceback
# import requests

logging.basicConfig(filename=f'{path}/log/logging.log', 
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# formatter = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s')
formatter = logging.Formatter('%(asctime)s - %(module)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)
logger = logging.getLogger(__name__)

def main():
    try:
        stats_list = []
        streak_list = []
        instrumnet_list = []
        # TICKER = 'BTC-USDT'
        account_equity = 100
        fee = 0.00 # in percentage
        flag = "0"  # Production trading: 0, Demo trading: 1
        data_engine = DataEngine(flag)
        spot_instruments = data_engine.get_tickers('SPOT')
        START_TIME = '2023-12-15 00:00:00'
        END_TIME = '2023-12-31 00:00:00'

        for index, row in spot_instruments.iterrows():

            inst_id = row['instId']
            if inst_id[-4:] == 'USDT':
                instrumnet_list.append(inst_id)

        def simulate(inst_id):
            btc_hisorical_price = pd.read_csv(f'{path}/btc_historical_cmc.csv', delimiter=';')
            historical_price = data_engine.get_historical_price(inst_id)
            btc_hisorical_price = btc_hisorical_price.sort_index(ascending=False)
            
            start_time = START_TIME
            end_time = END_TIME
            # slice historical price to the start and end time
            historical_price = historical_price.loc[start_time:end_time]
            simulator = Backtest(inst_id, historical_price=historical_price, account_equity=account_equity, fee=fee)
            stats = simulator.backtest()

            start_time = historical_price.index.min()
            end_time = historical_price.index.max()
            logging.info(f"Start time                                   : {start_time}")
            logging.info(f"End time                                     : {end_time}")
            logging.info(f"Total Days                                   : {end_time - start_time}")
            
            if stats is not None:
                stats['ticker'] = inst_id
                stats_list.append(stats)
            else:
                pass
            
        instrumnet_list = ['BTC-USDT', 'ETH-USDT','SOL-USDT', 'XRP-USDT', 'ADA-USDT', 
                        'DOGE-USDT', 'TRX-USDT', 'LINK-USDT', 'DOT-USDT', 'MATIC-USDT']
        
        instrumnet_list = ['BTC-USDT']

        # with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        #     futures = []
        #     for ins in instrumnet_list:
        #         futures.append(executor.submit(simulate, ins))
        #     for future in concurrent.futures.as_completed(futures):
        #         result = future.result()

        simulate('BTC-USDT')

        if len(stats_list) == 0:
            logging.info('No stats data')
        else:
            stats_df = pd.concat(stats_list)
            # join cmc_ranking_df and stats_df
            # cmc_ranking_df = data_engine.get_cmc_ranking()
            # cmc_ranking_df = cmc_ranking_df.drop_duplicates(subset=['symbol'])
            # stats_df['base_symbol'] = stats_df['ticker'].str.split('-').str[0]
            # stats_df = stats_df.merge(cmc_ranking_df, how='left', left_on='base_symbol', right_on='symbol')    
            # stats_df['market_cap_start'] = stats_df['fully_diluted_market_cap'].astype(float) / (1 + stats_df['Buy and Hold Return'])
            stats_df.to_csv('output/stats.csv')
        

        # send telegram message
        send_success_message('Backtest')
    except:
        send_fail_message('Backtest')

if __name__ == "__main__":
    main()

    # main()



# 1. Screening (at the eod ranking system)
# monitor top n instruments with 
# ideal case would be "imminent directional breakout (volatility)" 
# Execution engine: Market if touched (MIT) orders for "imminent trades"
# Volatility based screening
#  1. highest voliatility (volatility clusterings)
#  2. lowest volatility (consolidation before breakout)

# 2. Take profit and stop loss
# TP strategy affects screening rule
# TP strategy
# 1. Turtle Style
# 2. Trailing % TP (if fall below x% of the highest price, close position)
# 3. Trailing bar elapse TP (if x bars elapsed, close position)

# First in first out, which market ever hits the signal first, take it. Restrict maximum number of orders
# market 




