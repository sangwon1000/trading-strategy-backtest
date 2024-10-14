import pandas as pd
import datetime
# from data_feed import DataFeed
from okx.PublicData import PublicAPI
from okx.MarketData import MarketAPI
import logging
import typer
from typing import Optional
from data_engine.data_local import DataEngine

# import logging
# Develop Screener and use it for idea generation
# instruments vs tickers, use instruments which includes all trading pairs. not sure what tickers is for

logging.basicConfig(filename='log', 
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)
logger = logging.getLogger(__name__)

def main(
        initial_run: Optional[bool] = typer.Option(False, help="Initial Run", show_default="False"),
):
    print(initial_run)

if __name__ == '__main__':
    print("hello")


            

