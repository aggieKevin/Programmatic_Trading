from collections import defaultdict
import robin_stocks as r
import pickle
import pandas as pd
import yfinance as yf
from datetime import date,datetime
import time
import pytz
import logging
from StockTrade import StockTrade, model_1, model_2, two_points_line,convert_df_to_list

logger=logging.getLogger('trading')
logger.setLevel(logging.DEBUG)
formatter=logging.Formatter('%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s')

file_handler=logging.FileHandler(filename='trading.log',mode='w')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

if __name__=="__main__":

    #import getpass
    #psd = getpass.getpass('Enter your password')
    log=r.authentication.login('hejiakoo@gmail.com','hejia3382076@R')
    stockTrade=StockTrade('TQQQ',2000,0.1,104,30,model=model_1,realtrade=False)
    df=yf.download('TQQQ',start=date(2020,7,2), end=date(2020,9,11))
    current_list=convert_df_to_list(df)
    center_zone=pytz.timezone('US/Central')
    stockTrade.openShares+=1 # make up the error
    for p in current_list:
        print('---------------------------------------------------------------------')
        print('current price is :', p)
        stockTrade.tradeStock(p)
    
    stockTrade.realtrade=True
    logger.warning('set realtrade to true')
    while(True):
        ct=datetime.now(center_zone)
        if (ct.hour<7 or ct.hour >19):
            sleep_time=60
        else:
            sleep_time=2
        try:
            lastest_price=stockTrade.get_latest_price()
        except:
            logger.error('cannot get price, use old one')
        stockTrade.tradeStock(lastest_price)
        time.sleep(sleep_time)
        print(ct)
        print('latest price is ',lastest_price)