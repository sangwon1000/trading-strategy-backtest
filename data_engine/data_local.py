import os
import logging
from datetime import datetime, timezone
import pandas as pd
from sqlalchemy import types, create_engine
from pandas import json_normalize
import time
from okx.MarketData import MarketAPI

from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json

import os
from dotenv import load_dotenv
load_dotenv()

local_sql_string = os.getenv('CONNECTION_STRING_LOCAL')
cmc_api_key = os.getenv('CMC_API_KEY')

class DataEngine:
    def __init__(self, flag):
        path = os.path.dirname(os.path.abspath(__file__))
        self.engine = create_engine(local_sql_string)
        # print(pd.read_sql('select * from crypto_price_okx', self.engine))

        flag = "0"  # Production trading: 0, Demo trading: 1
        self.bar = '1H'
        self.marketDataAPI =  MarketAPI(flag=flag, debug=False)

        self.today = datetime.now().strftime("%Y-%m-%d")
        # for finding the earliest date
        now_utc = datetime.now(timezone.utc) 
        logging.info(f"Current Unix Timestamp in UTC: {now_utc}")
        current_unix_timestamp_ms = int(now_utc.timestamp() * 1000) // 86400000 * 86400000
        self.start_time = 0
        self.end_time = current_unix_timestamp_ms

    def get_cmc_ranking(self):
        df = pd.read_sql('select * from meta_data_cmc', self.engine)
        return df

    def update_cmc_ranking(self):
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
        parameters = {
        'start':'1',
        'limit':'5000',
        'convert':'USD'
        }
        headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': cmc_api_key,
        }

        session = Session()
        session.headers.update(headers)
        cmc_list = []
        try:
            response = session.get(url, params=parameters)
            data = json.loads(response.text)

            market_cap_ranking = pd.DataFrame(data['data'], index=None)

            for index, row in market_cap_ranking.iterrows():
                row['fully_diluted_market_cap'] = row['quote']['USD']['fully_diluted_market_cap']
                cmc_list.append(row.to_frame().T)

            cmc_rank_df = pd.concat(cmc_list)
            # cmc_rank_df.to_csv('./output/cmc.csv')
            # filter columns needed
            cmc_rank_df = cmc_rank_df[['symbol', 'num_market_pairs', 'date_added', 'cmc_rank', 'last_updated', 'fully_diluted_market_cap']]
            cmc_rank_df.to_sql(name='meta_data_cmc',
                        con=self.engine, index=False, if_exists='append')
            logging.info(f"CMC Ranking saved to database")
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            logging.info(e)

    def update_historical_price(self, inst_id):
        logging.info(f"Process Ticker: {inst_id}")
        latest_date_db = self.get_latest_date(inst_id)

        if latest_date_db is None:
            logging.info(f"Table for {inst_id} is empty")
            earliest_date = self.find_earliest_date(inst_id, self.bar, self.start_time, self.end_time)
            after_unix_timestamp_ms = earliest_date + ((3600 * 100 * 1000) + (3600 * 1000))
            before_unix_timestamp_ms = earliest_date
        else:
            logging.info(f"Table for {inst_id} is not empty")
            after_unix_timestamp_ms = latest_date_db + ((3600 * 100 * 1000) + (3600 * 1000))
            before_unix_timestamp_ms = latest_date_db
        
        time.sleep(0.03)
        ohlc_data = self.marketDataAPI.get_history_candlesticks(instId=inst_id, after=after_unix_timestamp_ms, before=before_unix_timestamp_ms, bar=self.bar, limit=100)
        
        ohlc_df = pd.DataFrame(ohlc_data['data'], columns=['ts', 'o', 'h', 'l', 'c', 'vol', 'volCcy', 'volCcyQuote', 'confirm'])
        # print(pd.to_datetime(ohlc_df['ts'].astype('int')/1000, unit='s'))
        # print(len(ohlc_df))
        # show datatype of each column in the dataframe
        ohlc_df['instId'] = inst_id
        # all columns, excluding instId, to number 
        ohlc_df[ohlc_df.columns[~ohlc_df.columns.isin(['instId'])]] = ohlc_df[ohlc_df.columns[~ohlc_df.columns.isin(['instId'])]].apply(pd.to_numeric)

        # composite primary key of instId and ts
        ohlc_df.to_sql(name='crypto_price_okx', dtype={'instId': types.VARCHAR(255)},
                       con=self.engine, index=False, if_exists='append')
        logging.info(f"Data for {inst_id} saved to database")

        return len(ohlc_df)

    def get_historical_price(self, inst_id):
        df = pd.read_sql(f'select * from crypto_price_okx where instId = "{inst_id}" ORDER BY ts ASC', self.engine, index_col='ts')
        df.index = pd.to_datetime(df.index.astype('int')/1000, unit='s')
        df = df.rename(columns={
                        "o": "open",
                        "h": "high",
                        "l": "low",
                        "c": "close",
                        "vol": "volume"
                    })
        return df

    def get_latest_date(self, inst_id):
        df = pd.read_sql(f'select max(ts) from crypto_price_okx where instId = "{inst_id}"', self.engine)
        if len(df) > 1:
            logging.info(f"Error: More than 1 row returned")
        elif len(df) == 0:
            logging.info(f"Error: No data returned")
            return None
        else:
            return df.values[0][0]
    
    def find_earliest_date(self, inst_id, bar, start_time, end_time):
        logging.info(f"Finding Earliest Date ... start_time: {start_time} end_time: {end_time}")
        if end_time - start_time <= 86400000:  # 86400000 milliseconds = 1 day
            logging.info(f"Earliest Date Found : {end_time, datetime.utcfromtimestamp(end_time / 1000).date()}")
            return end_time

        mid_time = ((start_time + (end_time - start_time) // 2) // 86400000) * 86400000
        
        response = self.marketDataAPI.get_history_candlesticks(
            instId=inst_id,
            bar=bar,
            limit=100,
            after=mid_time
        )
        # api rate limit
        time.sleep(1)
        
        if response['code'] == str(0):
            data = response['data']
            # print(data)
            if len(data) != 0:  # if there is data after the mid_time
                return self.find_earliest_date(inst_id, bar, start_time, mid_time)
            else:  # if there is no data after the mid_time
                return self.find_earliest_date(inst_id, bar, mid_time, end_time)
        else:
            print(f"Error: {response['code']}")
            return None

    def save_tickers(self, instType, uly='', instId='', instFamily=''):
        result = self.marketDataAPI.get_tickers(
            instType=instType,
            uly=uly,
            instFamily=instFamily
        )
        self.tickers_df = json_normalize(result['data'])
        self.tickers_df.to_csv(f'./output/{instType}_tickers_{self.today}.csv', index=False)
        print(f'tickers saved to ./output/{instType}_tickers_{self.today}.csv')
        return self.tickers_df

    def get_tickers(self, instType='SPOT'):
        spot_tickers = pd.read_csv(f'./output/{instType}_tickers_{self.today}.csv')
        return spot_tickers