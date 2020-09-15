import robin_stocks as r
import robin_stocks
import pandas as pd
import datetime
import json

def json_pprint(data): # data should be a list of dic or a dict
    print(json.dumps(data,indent=2))
"""
get return of a stock. The problem with this function is that a stock can have different instrument. e.g:
https://api.robinhood.com/instruments/fce3d82d-5c5a-4176-8c05-5f2a09b2a726/ and https://api.robinhood.com/instruments/3d75cadc-ee96-4d6f-81bc-7ea654364eb5/
both point to 'SQQQ'
"""
def return_by_symbol(symbol):
    #   a sybmol may have 
    records=r.orders.find_stock_orders(**{'symbol':symbol,'state':'filled'})
    # state can be 'filled','cancelled','confirmed'
    # 'cancel' can be None or a link. A link means the order is confirmed and can be cancelled
    buy_times=0
    accumulated_buy=0
    sell_times=0
    accumulated_sell=0
    profit=0
    
    for record in records:
        #print(record)
        if record['side']=='buy':
            buy_times+=1
            accumulated_buy+=float(record['executed_notional']['amount'])
        else:
            sell_times+=1
            accumulated_sell+=float(record['executed_notional']['amount'])
    current_holding=portfolio_by_symbol(symbol)
    print('current hodling of {} is {}'.format(symbol,current_holding))
    profit=current_holding+accumulated_sell-accumulated_buy
    return round(profit,2),current_holding,buy_times,sell_times

#get return of a stock by instrument
def return_by_instrument(instrument):
    records=r.orders.find_stock_orders(**{'instrument':instrument,'state':'filled'})
    # state can be 'filled','cancelled','confirmed'
    # 'cancel' can be None or a link. A link means the order is confirmed and can be cancelled
    buy_times=0
    accumulated_buy=0
    sell_times=0
    accumulated_sell=0
    profit=0
    
    for record in records:
        #print(record)
        if record['side']=='buy':
            buy_times+=1
            accumulated_buy+=float(record['executed_notional']['amount'])
        else:
            sell_times+=1
            accumulated_sell+=float(record['executed_notional']['amount'])
    current_holding=portfolio_by_instrument(instrument)
    #print('current hodling of {} is {}'.format(symbol,current_holding))
    profit=current_holding+accumulated_sell-accumulated_buy
    return round(profit,2),current_holding,buy_times,sell_times

# current equity value of a symbol
def portfolio_by_symbol(symbol):
    holdings=r.account.build_holdings()
    if symbol in holdings.keys():
        return round (float(holdings[symbol]['equity']),2)
    else: 
        return 0  

def portfolio_by_instrument(instrument):
    symbol=r.stocks.get_symbol_by_url(instrument)
    return portfolio_by_symbol(symbol)

#Returns a list of all the orders that have been processed for the account
def review_stock_profits():   
    all_stock_orders=r.orders.get_all_stock_orders(info='instrument')
    instrument_ever_traded=list(set(all_stock_orders)) # get the unique instrument url for each stock

    stocks_ever_traded= list(map(r.stocks.get_symbol_by_url,instrument_ever_traded))

    trades_results_all=list(map(return_by_instrument,instrument_ever_traded))
    col_names='profit,current_holding,buy_times,sell_times'.split(',')
    df2=pd.DataFrame(trades_results_all,index=stocks_ever_traded,columns=col_names)
    by_date=datetime.date.today().strftime('%Y-%m-%d')
    df2['by_date']=by_date # add date to df
    df2=df2.sort_values('profit')
    return df2


"""
--------------------------------------------------------
Functions for options
"""
from collections import defaultdict
def get_options_returns_list():
    all_options_orders=r.options.get_market_options()
    d=defaultdict(list)
    for order in all_options_orders:
        key=order['chain_symbol']
        process_value=float(order['processed_premium'])
        if process_value !=0:
            if order['legs'][0]['side']=='sell': 
                d[key].append(process_value)
            if order['legs'][0]['side']=='buy':
                d[key].append(-process_value)
    return d
                
def review_option_profit():
    d2=defaultdict(float)
    d=get_options_returns_list()
    for key in d:
        d2[key]=sum(d[key])
    return d2

def find_options_by_expiration_df(symbol,expirationDate,optionType):
    # return the options of a symbol at choosen expirationDate, in Dataframe format
    all_options=r.options.find_options_for_stock_by_expiration(symbol,expirationDate, optionType=optionType)
    cols_names=['chain_symbol','strike_price','open_interest','volume','ask_price','ask_size','bid_price','bid_size','adjusted_mark_price',
'break_even_price','expiration_date']
    df=pd.DataFrame(columns=cols_names)
    for option in all_options:
        row=list(map(lambda key:option[key],cols_names))
        row[1:4]=float(row[1]),float(row[2]),float(row[3])        
        df.loc[len(df)]=row
    return df

    
def find_options_all_df(symbol,optionType):
    all_options=r.options.find_tradable_options_for_stock(symbol, optionType=optionType)
    for item in all_options:
        market_data=r.options.get_option_market_data_by_id(item['id'])
        item.update(market_data) 
    cols_names=['chain_symbol','strike_price','open_interest','volume','ask_price','ask_size','bid_price','bid_size','adjusted_mark_price',
'break_even_price','expiration_date']
    df=pd.DataFrame(columns=cols_names)
    for option in all_options:
        row=list(map(lambda key:option[key],cols_names))
        row[1:4]=float(row[1]),float(row[2]),float(row[3])        
        df.loc[len(df)]=row
    return df
    

"""
option instrument data:
{"chain_id":"ad5b0734-7b34-4db0-9066-e2efe84c82e9","chain_symbol":"PDD","created_at":"2020-05-29T00:26:05.963470Z","expiration_date":"2020-07-10","id":"919bc398-e58d-43d4-87df-dec915b719b9","issue_date":"2018-08-08","min_ticks":{"above_tick":"0.10","below_tick":"0.05","cutoff_price":"3.00"},"rhs_tradability":"untradable","state":"active","strike_price":"85.0000","tradability":"tradable","type":"put","updated_at":"2020-05-29T00:26:05.963478Z","url":"https:\/\/api.robinhood.com\/options\/instruments\/919bc398-e58d-43d4-87df-dec915b719b9\/","sellout_datetime":"2020-07-10T18:45:00+00:00"}
"""

from requests import Session
def check_url_with_auth(url,token):    
    # Keeps track on if the user is logged in or not.
    LOGGED_IN = False
    # The session object for making get and post requests.
    SESSION = Session()
    SESSION.headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip,deflate,br",
        "Accept-Language": "en-US,en;q=1",
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        "X-Robinhood-API-Version": "1.0.0",
        "Connection": "keep-alive",
        "User-Agent": "Robinhood/823 (iphone; iOS 7.1.2, Scale/2.00)"
    }
    #url='https://api.robinhood.com/positions/5SR96732/91f7ea28-e413-4ca4-b9fa-91f5822f8b8d/'
    #url='https://api.robinhood.com/orders/d907ef09-b994-489b-a03b-9ca0f3ef6181/'

    SESSION.headers['Authorization']='Bearer {0}'.format(token)
    res=SESSION.get(url,params=payload)


