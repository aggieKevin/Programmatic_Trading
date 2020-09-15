# define the class of StockTrade

logger=logging.getLogger('trading')
logger.setLevel(logging.DEBUG)
formatter=logging.Formatter('%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s')

file_handler=logging.FileHandler(filename='trading.log',mode='w')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

def model_1(x,buy_or_sell):
    if buy_or_sell=='buy':
        ## buy model 1: price 100 factor 1; price 20 factor 2
        return round(-1/100*x+2,2) if x<=100 else 1
    elif buy_or_sell=='sell':
        #=IF(H5<100/0.9, -0.006*H5+1.5,0.9)
        return round(-0.006*x+1.5,2) if x/0.9<=100 else 0.9
    else:
        print('wrong parameter')
        
def model_2(x,buy_or_sell):
    if buy_or_sell=='buy':
        ## buy model 1: price 100 factor 1; price 20 factor 2
        return 1
    elif buy_or_sell=='sell':
        #=IF(H5<100/0.9, -0.006*H5+1.5,0.9)
        return 0.9
    else:
        print('wrong parameter')

def two_points_line(p1,p2):
    # y= a*x+b
    a=(p2[1]-p1[1])/(p2[0]-p1[0])
    b=p1[1]-(p2[1]-p1[1])/(p2[0]-p1[0])*p1[0]
    print('a is {0}, b is {1} , y = {0}*x + {1} '.format(a,b))

class StockTrade:
    def __init__(self,symbol,baseAmount,discountFactor,currentPrice,initialShares,model,realtrade):
        """
        readltrade(bool): if realtrade ==True, will send orders to robinhood;otherwise, it's a simulation
        """
        self.realtrade=realtrade
        self.symbol=symbol
        self.baseAmount=baseAmount
        self.discountFactor=discountFactor
        self.priceRange=self.generate_price_range()
        self.buy_factor_list=self.generate_factor_list(model,'buy') # buy model
        self.sell_factor_list=self.generate_factor_list(model,'sell') # sell model
        self.buy_amount_list=self.generate_buy_amount_list()
        self.sell_amount_list=self.generate_sell_amount_list()
        self.combined_lists=self.initialize_combined_list(currentPrice)
        self.openOrders={}
        self.openShares=initialShares
        self.orderNumber=0
        self.totalMoneyBuy=self.openShares*currentPrice
        self.totalmoneySell=0
        self.max_money_needed=self.totalMoneyBuy
        self.max_loss=0
        self.currentPrice=currentPrice
        #self.profit=0
        self.tradingRecords=defaultdict(list)
        self.update_tradingRecords(currentPrice,'buy',initialShares)# update the intial buy to account
        print('initialize, bought {0} shares at {1} worth {2}'.format(initialShares,currentPrice,initialShares*currentPrice))
        self.set_order()

                
    def generate_price_range(self): # return a list
        base=100
        less=100
        more=100
        l=[100]
        while more <200:
            more=more/(1-self.discountFactor)
            l.append(round(more,2))
        while less >20:
            less=less*(1-self.discountFactor)
            l.append(round(less,2))
        return sorted(l,reverse=True)
    
    def generate_factor_list(self,model,buy_or_sell):
        return [model(x,buy_or_sell) for x in self.priceRange]        
        
    def generate_buy_amount_list(self):
        return [round(self.baseAmount*i,2) for i in self.buy_factor_list]
    def generate_sell_amount_list(self):
        return [round(self.baseAmount*i,2) for i in self.sell_factor_list]
#     def initialize_labels(self,currentPrice):
#         l=[]
#         self.labels=['buy' if i>currentPrice-10 else 'sell' for i in self.priceRange]
    def get_profit(self,currentPrice):
        return round(self.openShares*currentPrice+self.totalmoneySell-self.totalMoneyBuy,2)
    
    def get_latest_price(self): # get the latest price of this symbel
        return float(r.stocks.get_latest_price(self.symbol)[0])
    
    def initialize_combined_list(self, currentPrice):
        """
        [{'price':* ,'sell':*, 'buy':*}]  item in list,
        sell: mean if it's allowed to sell at this price. affected by lower-price position buy order
        buy: mean if it's allowed to buy at his price. Affected by higher-price position sell order
        """
        l=[] 
        for i in range(len(self.priceRange)):
            price=self.priceRange[i]
            if self.priceRange[i]>=currentPrice:
                d={'price':price,'buy':False,'buy_amount':self.buy_amount_list[i],'sell':True,'sell_amount':self.sell_amount_list[i]}
            else:
                d={'price':price,'buy':True,'buy_amount':self.buy_amount_list[i],'sell':False,'sell_amount':self.sell_amount_list[i]}
            l.append(d)
#         for price in self.priceRange:
#             if price >=currentPrice:
#                 d={'price':price,'sell':True, 'buy':False}
#             else:
#                 d={'price':price,'sell':False, 'buy':True}
#             l.append(d)
        return l       
                
    def sell_setting(self,position):

        logger.info('sell setting: ')
        price=self.priceRange[position]
        amount=self.sell_amount_list[position]
        shares=round(amount/price)
        self.check_shares_avai_for_sale(shares)
        logger.info('sell {0} shares, amount {1} at {2}'.format(shares,amount,price))
        #r.orders.order_sell_limit('TQQQ',quantity=shares,limitPrice=price,extendedHours=True)
        self.openOrders.update({'sell':[{'shares':shares,'amount':amount,'price':price,'position':position}]})
        
    def buy_setting(self,position):
        logger.info('buy setting: ')
        price=self.priceRange[position]
        amount=self.buy_amount_list[position]
        shares=round(amount/price)
        logger.info('buy {0} shares, amount {1} at {2}'.format(shares,amount,price))
        #r.orders.order_buy_limit('TQQQ',quantity=shares,limitPrice=price,extendedHours=True)
        # openOrders is a dictionary, whose keys include 'buy' and 'sell'
        self.openOrders.update({'buy':[{'shares':shares,'amount':amount,'price':price,'position':position}]})
  
    def set_order(self):
        logger.info('---------set up open orders-----------')
        for j in range(len(self.priceRange)):
            if self.combined_lists[j]['buy']==True:
                self.buy_setting(j)
                break
        for k in range(len(self.priceRange)-1,-1,-1):
            if self.combined_lists[k]['sell']==True:
                self.sell_setting(k)
                break
        if self.realtrade==True:
            self.send_orders_to_rb() # send orders to robinhood
        
    def send_orders_to_rb(self):
        logger.warning('send orders to robinhood')
        r.orders.cancel_all_stock_orders() # clean all orders
        open_orders=self.openOrders
        limit_put_args={'symbol':'TQQQ','quantity':open_orders['buy'][0]['shares'],'limitPrice':open_orders['buy'][0]['price'],'extendedHours':True}
        r.orders.order_buy_limit(**limit_put_args)  # make the limit buy order 
        limit_sell_args={'symbol':'TQQQ','quantity':open_orders['sell'][0]['shares'],'limitPrice':open_orders['sell'][0]['price'],'extendedHours':True}
        r.orders.order_sell_limit(**limit_sell_args)# make the limit sell order
        logger.warning('---confirm the orders---')
        logger.warning(r.orders.get_all_open_stock_orders()) # check the orders
    def market_buy_rb(self,shares):
        logger.warning('market buy {} shares in robinhood'.format(shares))
        market_buy_args={'symbol':self.symbol,'quantity':shares,'extendedHours':True}
        r.orders.order_buy_market(**market_buy_args)
    
    def update_tradingRecords(self,price,action,shares):
        self.tradingRecords[price].append([action,shares])
    def update_openShares(self,action,shares):
        self.openShares=self.openShares-shares if action=='sell' else self.openShares+shares
    def update_labels(self,position,action,b):
        self.combined_lists[position].update({action:b})
    def check_shares_avai_for_sale (self,shares_to_sell): 
        '''
        when not enough shares available for sale, due to price keeping moving higher, buy some shares one time
        '''
        if self.openShares<=shares_to_sell+1:
            logger.warning('-------------')
            logger.warning('current share is {}, not enough shares in hand available for sale'.format(self.openShares))
            self.increase_shares(int(2*self.baseAmount/self.currentPrice))
            logger.warning('-------------')        
        
    def increase_shares(self,shares):
        logger.warning('buy {0} shares at {1} before open the sell order'.format(shares,self.currentPrice))
        self.update_tradingRecords(self.currentPrice,'buy',shares)
        self.update_openShares('buy',shares)
        self.totalMoneyBuy+=self.currentPrice*shares
        self.update_max_money_needed()
        if self.realtrade==True:
            self.market_buy_rb(shares)
        
    def update_max_money_needed(self):
        self.max_money_needed=max(self.max_money_needed,self.totalMoneyBuy-self.totalmoneySell)
    def update_max_loss_value(self,currentPrice):
        self.max_loss=min(self.get_profit(currentPrice),self.max_loss)                  
    
    def tradeStock(self,currentPrice):
        self.currentPrice=currentPrice
        #print('profit is ,', self.get_profit(currentPrice))
        self.update_max_loss_value(currentPrice)
        if currentPrice >self.openOrders['sell'][0]['price']:
            shares,amount,price,position=self.openOrders['sell'][0].values()
            action='sell'
            logger.info('---------execute order--------')
            #print('current price is ',currentPrice)
            logger.info('before trade, current shares: {}'.format(self.openShares))
            logger.info('now price {0}, sold {1} shares at {2} worth {3}'.format(currentPrice,shares,price,amount))
            #update tradingRecords
            self.totalmoneySell+=price*shares
            self.openOrders.update({'sell':[]})  # erase the open sell order as it is fulfilled
            self.orderNumber+=1
            self.update_tradingRecords(price,action,shares)  
            self.update_openShares(action,shares)
            self.update_labels(position,'sell',False)
            self.update_labels(position+1,'buy',True)
            logger.info('after trade, current shares: {}'.format(self.openShares))
            [logger.info(i) for i in self.combined_lists]
            #print(*self.combined_lists,sep='\n')
            # open new orders
            self.set_order()
            
            
        elif currentPrice<self.openOrders['buy'][0]['price']:  # currentPrice < openOrder buy limit price
            shares,amount,price,position=self.openOrders['buy'][0].values()
            action='buy'
            logger.info('---------execute order--------')
            #print('current price is ',currentPrice)
            logger.info('before trade, current shares: {}'.format(self.openShares))
            logger.info('now price {0}, bought {1} shares at {2} worth {3}'.format(currentPrice,shares,price,amount))
            #update
            self.totalMoneyBuy+=price*shares
            self.update_max_money_needed()
            logger.info('money required {}'.format(self.max_money_needed))
            self.openOrders.update({'buy':[]}) # erase the open buy order as it is fulfilled 
            self.orderNumber+=1
            self.update_tradingRecords(price,action,shares)  
            self.update_openShares(action,shares)          
            self.update_labels(position,'buy',False)
            self.update_labels(position-1,'sell',True)
            logger.info('after trade, current shares: {}'.format(self.openShares))
            [logger.info(i) for i in self.combined_lists]
            # open new orders
            self.set_order() 
        else:
            print('---------no execute --------')