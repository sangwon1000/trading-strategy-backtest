import pandas as pd
import typer
from typing import Optional
import os
import logging
# from datetime import datetime, timezone
# from dotenv import load_dotenv
# load_dotenv()
from data_local import DataEngine
# from okx.MarketData import MarketAPI
# import datetime
import time
import sys
path = os.path.dirname(__file__)
sys.path.append(os.path.join(path, '..'))

logging.basicConfig(filename=f'{path}/log/logging.log', 
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)
logger = logging.getLogger(__name__)

def main(
        run_date: Optional[str] = typer.Option(None, help="Run Date", show_default="Today's Date"),
        # initial_run: Optional[bool] = typer.Option(False, help="Initial Run", show_default="False"),
):
    # print(run_date)
    # print(initial_run)

    flag = "0"  # Production trading: 0, Demo trading: 1
    UPDATE_HISTORICAL = False
    data_engine = DataEngine(flag)

    # inst_id = 'BTC-USDT'
    
    def update_historical_price_api(inst_id):
        count = 0
        start = time.time()
        while True:
            # Rate Limit: 20 requests per 2 seconds
            res = data_engine.update_historical_price(inst_id)
            count += 1
            end = time.time()
            elapsed = end - start
            # print(elapsed)
            if count == 18:
                sleep_time = 2 - elapsed + 0.5
                if sleep_time < 0:
                    sleep_time = 0
                time.sleep(sleep_time)
                count = 0
                start = time.time()
            if res == 0:
                logging.info(f"Data for {inst_id} is up to date")
                break  

    # https://www.okx.com/docs-v5/en/?python#public-data-rest-api-get-instruments
    data_engine.save_tickers(instType='SPOT')
    data_engine.save_tickers(instType='SWAP')
    data_engine.update_cmc_ranking()
    if UPDATE_HISTORICAL is True:
        spot_instruments = data_engine.get_tickers('SPOT')
        for index, row in spot_instruments.iterrows():
            inst_id = row['instId']
            if inst_id[-4:] == 'USDT':
            # if inst_id == 'BTC-USDT':
                update_historical_price_api(inst_id)


if __name__ == '__main__':
    typer.run(main)

# feed
        # if row['instId'] == 'BTC-USDT':
        #     instId = row['instId']
        #     flag = "0"  # Production trading: 0, Demo trading: 1
        #     marketDataAPI =  MarketAPI(flag=flag, debug=False)
        #     # Retrieve order book of the instrument
        #     # https://www.okx.com/docs-v5/en/#order-book-trading-market-data-get-order-book
        #     # Rate Limit: 40 requests per 2 seconds

        #     print(instId)
        #     result = marketDataAPI.get_orderbook(
        #         instId=instId,
        #         sz=1
        #     )
        #     # epoch to datetime
        #     gen_time = datetime.datetime.fromtimestamp(int(result['data'][0]['ts'])/1000)
        #     print(gen_time)
        #     print(result['code'])
        #     print(result['msg'])
        #     print(result['data'][0])
        #     print(result['data'][0]['ts'])