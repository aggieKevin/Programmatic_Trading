def get_stock_volatility_data_for_period(symbol,start_date,end_date):
    #start_date,end_date str, 'yyyy-mm-dd'
    #data from start_date is included, from end_date is not included
    stock_data=yf.download(symbol,start=start_date,end=end_date)
    lowest,highest=round(np.min(stock_data['Close']),2),round(np.max(stock_data['Close']),2)
    current=stock_data['Close'][-1]
    crt_lowest_growth=round(current/lowest-1,4)
    crt_highest_drop=round(current/highest-1,4)
    intraday_volatility=((stock_data['High']-stock_data['Low'])/stock_data['Close']).mean()
    interday_volatility=abs(stock_data['Close'].pct_change()).mean()
    start_date_str=start_date.strftime('%Y-%m-%d')    
    return [lowest,highest,current,crt_lowest_growth,crt_highest_drop,intraday_volatility,interday_volatility,start_date,end_date]

def stocks_volatility_data_for_period (symbols,start_date,end_date):
    #symbols: a list of stocks
    #
    l=[]
    for stock in symbols:
        print('symbol is ',stock)
        stock_data=get_stock_volatility_data_for_period(stock,start_date,end_date)
        l.append(stock_data)
    col_names='lowest highest current crt_lowest_growth crt_highest_drop intraday_volatility interday_volatility start_date end_date'.split()
    df=pd.DataFrame(l,index=symbols,columns=col_names)
    return df