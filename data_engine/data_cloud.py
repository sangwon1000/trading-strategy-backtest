import logging
import pandas as pd
from sqlalchemy import types, create_engine
#dot env import
import os
from dotenv import load_dotenv
load_dotenv()

class DataEngineCloud:
    def __init__(self):
        # path = os.path.dirname(os.path.abspath(__file__))
        connection_string = os.getenv('CONNECTION_STRING_SUPABASE')
        self.engine = create_engine(connection_string)
        
    def update_historical_price(self, df):
        logging.info(f"Updating supabase historical_price")
        df.to_sql(name='historical_price', con=self.engine, index=True, if_exists='replace')
        logging.info(f"supabase historical_price is updated")