from binance.client import Client
from binance.enums import *
from decimal import *
import json, time
from Order import Order


AVG_BID_INCREASE = .025
CACHE_LIFESPAN = .9# seconds
TRADE_TAX = .001 #Binance's .1% fee


#---- Binance API information
api_key = ""
api_secret = ""

client = Client(api_key, api_secret)


"""
for i in range(1, 10):
    local_time1 = int(time.time() * 1000)
    server_time = client.get_server_time()
    diff1 = server_time['serverTime'] - local_time1
    local_time2 = int(time.time() * 1000)
    diff2 = local_time2 - server_time['serverTime']
    print("local1: %s server:%s local2: %s diff1:%s diff2:%s" % (local_time1, server_time['serverTime'], local_time2, diff1, diff2))
    time.sleep(2)






exit()
"""


#--------------------Cache
class DataCache:
    priceData = None
    lastPriceUpdate = 0

    orderBookData = None
    lastOrderBookUpdate = 0

    assetBalanceData = {}
    lastBalanceUpdate = {}

    symbolInfo = {}
    lastSymbolUpdate = {}

    ordersInfo = {}
    lastOrdersInfo = {}

    recentTrades = {}
    lastTradesUpdate = {}

    dayTickerData = None
    lastDayTickerUpdate = 0




 #--------------------Orders



#------------------Orders
def order_buy(pair, quantity, price):
    print("--placing order for {} {} at {} each".format(quantity, pair, price))
    order = client.create_order(
        symbol=pair,
        side=SIDE_BUY,
        type=ORDER_TYPE_LIMIT,
        timeInForce=TIME_IN_FORCE_GTC,
        quantity=quantity,
        price=price)

    data = json.dumps(order)
    data = json.loads(data)
    return data['orderId']

def order_sell(pair, quantity, price):

    order = client.create_order(
        symbol=pair,
        side=SIDE_SELL,
        type=ORDER_TYPE_LIMIT,
        timeInForce=TIME_IN_FORCE_GTC,
        quantity=quantity,
        price=price)

    data = json.dumps(order)
    data = json.loads(data)
    return data['orderId']

def order_status(pair, orderId):
    return client.get_order( symbol = pair, orderId = orderId)

def order_abort(pair, orderId):
    try:
        return client.cancel_order( symbol = pair, orderId = orderId)
    except:
        print ("Unexpected error: {}".format(sys.exc_info()[0]))



#----------------Market Info
def get_orderbook_tickers():
    if time.time() - DataCache.lastOrderBookUpdate >= CACHE_LIFESPAN:
        #fetch new
       # print("GETTING FRESH ORDERBOOK")
        tickers = client.get_orderbook_tickers()
        DataCache.orderBookData = tickers
        DataCache.lastOrderBookUpdate = time.time()
    else:
        #use cached
        tickers = DataCache.orderBookData
    return tickers

def get_24hr_ticker():
    if time.time() - DataCache.lastDayTickerUpdate >= CACHE_LIFESPAN:
        #fetch new
        #print("GETTING FRESH 24HR")
        ticker = client.get_ticker()
        DataCache.dayTickerData = ticker
        DataCache.lastDayTickerUpdate = time.time()
    else:
        #use cached
        ticker = DataCache.dayTickerData

    return ticker

def get_symbol_data(symbol):
    if symbol not in DataCache.symbolInfo:
        DataCache.symbolInfo[symbol] = None
        DataCache.lastSymbolUpdate[symbol] = 0

    if time.time() - DataCache.lastSymbolUpdate[symbol] >= CACHE_LIFESPAN:
        #print("GETTING FRESH SYMBOL DATA")
        info = client.get_symbol_info(symbol)
        DataCache.symbolInfo[symbol] = info
        DataCache.lastSymbolUpdate[symbol] = time.time()
    else:
        info = DataCache.symbolInfo[symbol]

    return info

def get_recent_trades(pair):
    if pair not in DataCache.recentTrades:
        DataCache.recentTrades[pair] = None
        DataCache.lastTradesUpdate[pair] = 0

    if time.time() - DataCache.lastTradesUpdate[pair] >= CACHE_LIFESPAN:
        #print("GETTING FRESH RECENT TRADES")
        info = client.get_recent_trades(symbol=pair)
        DataCache.recentTrades[pair] = info
        DataCache.lastTradesUpdate[pair] = time.time()
    else:
        info = DataCache.recentTrades[pair]

    return info[::-1]

def get_pair_volume(pair):
    ticker = get_24hr_ticker()

    for p in ticker:
        if p['symbol'] == pair:
            return Decimal(p['quoteVolume'])

def get_price(pair):

    if time.time() - DataCache.lastPriceUpdate >= CACHE_LIFESPAN:
        #fetch new
        print("GETTING FRESH PRICE")
        prices = client.get_all_tickers()
        DataCache.priceData = prices
        DataCache.lastPriceUpdate = time.time()
    else:
        #use cached
        prices = DataCache.priceData

    p = None
    for p in prices:
        if p['symbol'] == pair:
            return Decimal(p['price'])

def get_orders_data(pair):
    if pair not in DataCache.ordersInfo:
        DataCache.ordersInfo[pair] = None
        DataCache.lastOrdersInfo[pair] = 0

    if time.time() - DataCache.lastOrdersInfo[pair] >= CACHE_LIFESPAN:
        #print("GETTING FRESH ORDERS DATA")
        info = client.get_order_book(symbol=pair)
        DataCache.ordersInfo[pair] = info
        DataCache.lastOrdersInfo[pair] = time.time()
    else:
        info = DataCache.ordersInfo[pair]

    return info

def get_list_of_bids(pair):
    data = get_orders_data(pair)

    bids = []
    for d in data['bids']:
        bids.append((d[0], d[1]))

    return bids

def get_list_of_asks(pair):
    data = get_orders_data(pair)

    asks = []
    for d in data['asks']:
        asks.append((d[0], d[1]))

    return asks

#------------Account Info
def get_current_balance(symbol):
    if symbol not in DataCache.assetBalanceData:
        DataCache.assetBalanceData[symbol] = None
        DataCache.lastBalanceUpdate[symbol] = 0

    if time.time() - DataCache.lastBalanceUpdate[symbol] >= CACHE_LIFESPAN:
        print("GETTING FRESH BALANCE")
        balance = client.get_asset_balance(asset=symbol)
        DataCache.assetBalanceData[symbol] = balance
        DataCache.lastBalanceUpdate[symbol] = time.time()
    else:
        balance = DataCache.assetBalanceData[symbol]

    return balance['free']


#-----------Calculations
def calculate_spread_percentage(bid, ask, price):
    spread = Decimal(ask - bid)
    return Decimal(spread / price) * 100



class Symbol:

    def __init__(self, data):
        self.pairSymbol = data['symbol']
        self.minorSymbol = data['baseAsset']
        self.majorSymbol = data['quoteAsset']
        self.minorPrecision = data['baseAssetPrecision']
        self.majorPrecision = data['quotePrecision']

        self.minPrice = Decimal(data['filters'][0]['minPrice'])
        self.maxPrice = Decimal(data['filters'][0]['maxPrice'])
        self.tickSize = Decimal(data['filters'][0]['tickSize'])

        self.minQuantity = Decimal(data['filters'][1]['minQty'])
        self.maxQuantity = Decimal(data['filters'][1]['maxQty'])
        self.stepSize = Decimal(data['filters'][1]['stepSize'])

    def increment_bid(self, bid):
        bid += self.tickSize
        return bid

    def decrement_ask(self, ask):
        ask -= self.tickSize
        return ask

    def get_best_bid(self):
        tickers = get_orderbook_tickers()

        for t in tickers:
            if t['symbol'] == self.pairSymbol:
                return Decimal(t['bidPrice'])

    def get_best_ask(self):
        tickers = get_orderbook_tickers()

        for t in tickers:
            if t['symbol'] == self.pairSymbol:
                return Decimal(t['askPrice'])

    def get_max_buyable_quant(self, price, amountToSpend):

        if self.stepSize >= 1:
            step, _ = str(self.stepSize).split(".")
        else:
            step = self.stepSize
            step = "{}".format(step)
            step = step.strip('0')

        amountToBuy = amountToSpend/price
        amountToBuy = amountToBuy.quantize(Decimal(step), rounding=ROUND_DOWN)  #Magic truncation
        return amountToBuy

    def get_max_sellable_quant(self, amount):
        amnt = Decimal(amount)
        if self.stepSize >= 1:
            step, _ = str(self.stepSize).split(".")
        else:
            step = self.stepSize
            step = "{}".format(step)
            step = step.strip('0')
        amnt = amnt.quantize(Decimal(step), rounding=ROUND_DOWN)
        return amnt

    def get_price(self):
        if time.time() - DataCache.lastPriceUpdate >= CACHE_LIFESPAN:
            #fetch new
            print("Fetching new data")
            prices = client.get_all_tickers()
            DataCache.priceData = prices
            DataCache.lastPriceUpdate = time.time()
        else:
            #use cached
            print("using cached data")
            prices = DataCache.priceData

        p = None
        for p in prices:
            if p['symbol'] == self.pairSymbol:
                return Decimal(p['price'])

    def get_balance(self):
        return get_current_balance(self.minorSymbol)

    def get_spread(self):
        tickers = get_orderbook_tickers()

        for t in tickers:
            if t['symbol'] == self.pairSymbol:
                return 100 * (Decimal(t['askPrice']) - Decimal(t['bidPrice']))

    def get_spread_percentage(self):
        spread = self.get_spread()
        price = self.get_price()
        return Decimal(spread/price)

    def buy(self, quantity, price):
        return order_buy(self.pairSymbol, quantity, price)

    def buy_max(self, price, amountToSpend):
        quantity = self.get_max_buyable_quant(price, amountToSpend)
        return self.buy(quantity, price), quantity

    def sim_buy_max(self, price, amountToSpend):
        quantity = self.get_max_buyable_quant(price, amountToSpend)
        return '1111', quantity

    def sell(self, quantity, price):
        return order_sell(self.pairSymbol, quantity, price)

    def sell_max(self, price):
        balance = self.get_balance()
        quantity = self.get_max_sellable_quant(balance)
        return self.sell(quantity, price)

    def sim_sell_max(self, price, quant):
        #balance = self.get_balance()
        quantity = self.get_max_sellable_quant(quant)
        return '2222', quantity

    def abort_order(self, orderId):
        return order_abort(self.pairSymbol, orderId)

    def order_status(self, orderId):
        return order_status(self.pairSymbol, orderId)

    def get_volume(self):
        return get_pair_volume(self.pairSymbol)







class BinanceBidOrder:

    sym = None
    orderId = None

    bid = 0
    amountToSpend = 0
    amountSpent = 0

    prepared = False
    simulating = False

    standAlone = False

    quantCurrentlyOrdered = 0
    quantBoughtTotal = 0
    quantBoughtPartial = 0

    quantBeforeMe = 0


    #lastTradeID = 0
    oldTrades = None


    def __init__(self, symbol, amountToSpend):
        self.sym = symbol
        self.amountToSpend = Decimal(amountToSpend)


    def prepare(self):
        if not self.prepared:
            bestBid = self.sym.get_best_bid()
            #self.bid = self.sym.increment_bid(bestBid)
            self.bid = bestBid
            self.prepared = True
        else:
            print("Trying to prepare an already prepared order")

    def prepare_sim(self):
        self.simulating = True
        self.prepare()

    def place(self):
        if not self.prepared:
            print("Trying to place an unprepared order. .Prepare() the order first.")
            return

        if not self.simulating:
            self.orderId, quant = self.sym.buy_max(self.bid, self.amountToSpend - self.amountSpent)
        else:
            self.orderId, quant = self.sym.sim_buy_max(self.bid, self.amountToSpend - self.amountSpent)


        prev = self.quantCurrentlyOrdered
        self.quantCurrentlyOrdered = quant
        self.quantBoughtPartial = 0

        if prev != self.quantCurrentlyOrdered:
            print("Placed order for {} {} @ {}".format(self.quantCurrentlyOrdered, self.sym.minorSymbol, self.bid))




    def abort(self):
        if self.simulating:
            self.orderId = None
            self.bid = 0
            return

        if self.orderId:
            self.sym.abort_order(self.orderId)
        else:
            print("Trying to abort without an active order. Prepare and Place an order first")





    def update(self):


        #Up here would be soemthing like
        #    orderFilled = __get_offer_state(offerId)
        #   if offerFilled then return True

     #   if not self.orderId:
     #       print("Trying to improve a bid without having an active order")
     #       return

        if self.simulating:
            trades = get_recent_trades(self.sym.pairSymbol)
            if self.oldTrades == None:
                self.oldTrades = []
                for t in trades:
                    self.oldTrades.append(t['id'])

           # if self.lastTradeID == 0:
           #     self.lastTradeID = trades[0]['id']

            #print(trades)
            for t in trades:
                #if t['id'] == self.lastTradeID:
                #    self.lastTradeID = trades[0]['id']
                 #   break
                if t['id'] in self.oldTrades:
                    break;
                self.oldTrades.append(t['id'])



                if t['price'] <= str(self.bid):
                    saleQuant = Decimal(t['qty'])
                    print("\n>>New Trade<<")
                    print("RawQuant: {} QuantBeforeMe: {} TradePrice: {} MyPrice: {}".format(saleQuant, self.quantBeforeMe, t['price'], self.bid))

                    diff = saleQuant - self.quantBeforeMe
                    self.quantBeforeMe = max(self.quantBeforeMe - saleQuant, 0)
                    print("New QuantBeforeMe: {}".format(self.quantBeforeMe))
                    print("Overflow that goes to me: {}".format(max(0, diff)))
                    if diff <= 0:
                        continue
                    saleQuant = diff
                    print("So, actual saleQuant for calcs is: {}".format(saleQuant))


                    if (self.quantCurrentlyOrdered - self.quantBoughtPartial) - saleQuant > 0:
                        self.amountSpent += saleQuant * self.bid
                        self.quantBoughtPartial += saleQuant
                        self.quantBoughtTotal += saleQuant

                        print("------PARITAL FILL: Bid: {} Total Bought: {} Partial Bought: {} ETH spent: {}\n".format(self.bid, self.quantBoughtTotal, self.quantBoughtPartial, self.amountSpent))

                    else:  # saleQuant - () <= 0:
                        quantBought = self.quantCurrentlyOrdered - self.quantBoughtPartial
                        self.amountSpent += quantBought * self.bid
                        self.quantBoughtPartial += quantBought
                        self.quantBoughtTotal += quantBought
                        print("------COMPLETE FILL: Bid: {} Total Bought: {} Partial Bought: {} ETH spent: {}\n".format(self.bid, self.quantBoughtTotal, self.quantBoughtPartial, self.amountSpent))
                        #self.lastTradeID = trades[0]['id']
                        return True
            #self.lastTradeID = trades[0]['id']









        allBids = get_list_of_bids(self.sym.pairSymbol)
        newBid = self.bid

        nextVol = 0
        for b in allBids:
            nextBid = Decimal(b[0])
            nextVol = Decimal(b[1])
            #print("{} -- {}".format(self.bid, b[0]))


            if nextBid > self.bid:
                if (nextBid - self.bid)/self.bid <= AVG_BID_INCREASE:
                   # print("New Higher Bid: {}".format(nextBid))
                    newBid = nextBid
                    break
            elif nextBid == self.bid:
                if (self.quantCurrentlyOrdered - self.quantBoughtPartial == Decimal(b[1])):
                    #print("Standing Alone")
                    self.standAlone = True

                else:
                    #print("Not Alone")
                    self.standAlone = False
                    break
            elif nextBid < self.bid:
            #    if (self.bid - nextBid)/nextBid <= AVG_BID_INCREASE:
                #print("We're Too High! New low bid: {}".format(nextBid))
                newBid = nextBid
                break

        if newBid != self.bid:
            self.quantBeforeMe = nextVol
            self.bid = newBid
            print("Updating bid: {}. {} {} before me".format(newBid, self.quantBeforeMe, self.sym.minorSymbol))
            self.place()

        return False




class BinanceAskOrder:

    sym = None
    orderId = None

    amountEarned = 0
    ask = 0

    prepared = False
    simulating = False

    standAlone = False

    quantCurrentlySelling = 0
    quantSoldTotal = 0
    quantSoldPartial = 0



    #lastTradeID = 0
    oldTrades = None

    quantBeforeMe = 0


    def __init__(self, symbol, amountToSell):
        self.sym = symbol
        self.amountToSell = amountToSell



    def prepare(self):
        if not self.prepared:
            bestAsk = self.sym.get_best_ask()
            #self.ask = self.sym.increment_ask(bestAsk)
            self.ask = bestAsk
            self.prepared = True
        else:
            print("Trying to prepare an already prepared order")

    def prepare_sim(self):
        self.simulating = True
        self.prepare()

    def place(self):
        if not self.prepared:
            print("Trying to place an unprepared order. .Prepare() the order first.")
            return

        if not self.simulating:
            self.orderId, quant = self.sym.sell_max(self.ask)
        else:
            self.orderId, quant = self.sym.sim_sell_max(self.ask, (self.amountToSell - self.quantSoldTotal))


        prev = self.quantCurrentlySelling
        self.quantCurrentlySelling = quant
        self.quantSoldPartial = 0

        if prev != self.quantCurrentlySelling:
            print("Placed order to sell {} {} @ {}".format(self.quantCurrentlySelling, self.sym.minorSymbol, self.ask))




    def abort(self):
        if self.simulating:
            self.orderId = None
            self.ask = 0
            return

        if self.orderId:
            self.sym.abort_order(self.orderId)
        else:
            print("Trying to abort without an active order. Prepare and Place an order first")





    def update(self):


        #Up here would be soemthing like
        #    orderFilled = __get_offer_state(offerId)
        #   if offerFilled then return True

     #   if not self.orderId:
     #       print("Trying to improve a ask without having an active order")
     #       return
       
        if self.simulating:
            trades = get_recent_trades(self.sym.pairSymbol)
            if self.oldTrades == None:
                self.oldTrades = []
                for t in trades:
                    self.oldTrades.append(t['id'])
          #  if self.lastTradeID == 0:
          #      self.lastTradeID = trades[0]['id']
            #print(trades)
            for t in trades:
                if t['id'] in self.oldTrades:
                    break;
                self.oldTrades.append(t['id'])



                #print("NEW TRADE: {}  MY ASK: {}".format(t['price'], str(self.ask)))
                if t['price'] >= str(self.ask):
                    saleQuant = Decimal(t['qty'])
                    print(">>New Trade<<")
                    print("RawQuant: {} QuantBeforeMe: {} TradePrice: {} MyPrice: {}".format(saleQuant, self.quantBeforeMe, t['price'], self.ask))

                    diff = saleQuant - self.quantBeforeMe
                    self.quantBeforeMe = max(self.quantBeforeMe - saleQuant, 0)
                    print("New QuantBeforeMe: {}".format(self.quantBeforeMe))
                    print("Overflow that goes to me: {}".format(max(0, diff)))
                    if diff <= 0:
                        continue
                    saleQuant = diff
                    print("So, actual saleQuant for calcs is: {}".format(saleQuant))


                    if (self.quantCurrentlySelling - self.quantSoldPartial) - saleQuant > 0:
                        self.amountEarned += saleQuant * self.ask
                        self.quantSoldPartial += saleQuant
                        self.quantSoldTotal += saleQuant

                        print("------PARITAL FILL: Ask: {} Total Sold: {} Partial Sold: {} ETH earned: {}".format(self.ask, self.quantSoldTotal, self.quantSoldPartial, self.amountEarned))

                    else:  # saleQuant - () <= 0:
                        quantSold = self.quantCurrentlySelling - self.quantSoldPartial
                        self.amountEarned += quantSold * self.ask
                        self.quantSoldPartial += quantSold
                        self.quantSoldTotal += quantSold
                        print("------COMPLETE FILL: Ask: {} Total Sold: {} Partial Sold: {} ETH earned: {}".format(self.ask, self.quantSoldTotal, self.quantSoldPartial, self.amountEarned))
                        #self.lastTradeID = trades[0]['id']
                        return True
           # self.lastTradeID = trades[0]['id']
            





        allAsks = get_list_of_asks(self.sym.pairSymbol)
        newAsk = self.ask
        nextVol = 0
        for b in allAsks:
            nextAsk = Decimal(b[0])
            nextVol = Decimal(b[1])

            #print("{} -- {}".format(self.ask, b[0]))


            if nextAsk < self.ask:
                if (nextAsk - self.ask)/self.ask <= AVG_BID_INCREASE:
                   # print("New Better Ask: {}".format(nextAsk))
                    newAsk = nextAsk
                    break
            elif nextAsk == self.ask:
                if (self.quantCurrentlySelling - self.quantSoldPartial == nextVol):
                    #print("Standing Alone")
                    self.standAlone = True

                else:
                    #print("Not Alone")
                    self.standAlone = False
                    break
            elif nextAsk > self.ask:
            #    if (self.ask - nextAsk)/nextAsk <= AVG_ASK_INCREASE:
                #print("We're Too High! New low ask: {}".format(nextAsk))
                newAsk = nextAsk
                break





        if newAsk != self.ask:
            self.quantBeforeMe = nextVol
            self.ask = newAsk
            print("Updating ask: {}. {} {} before me".format(newAsk, self.quantBeforeMe, self.sym.minorSymbol))
            self.place()

        return False













def create_bid_order(tradePair, amountToSpend):
    symData = get_symbol_data(tradePair)
    sym = Symbol(symData)
    return BinanceBidOrder(sym, amountToSpend)


def create_ask_order(tradePair, amountToSell):
    symData = get_symbol_data(tradePair)
    sym = Symbol(symData)
    return BinanceAskOrder(sym, amountToSell)


def get_best_spread(symbol):

    tickers = get_orderbook_tickers()

    data = json.dumps(tickers)
    data = json.loads(data)

    maxSpread = 0
    bestPair = ""
    for s in data:
        pair = s['symbol']
        if symbol not in pair:
            continue
        if "USDT" in pair:
            continue

        if get_pair_volume(pair) < 2000 or get_pair_volume(pair) > 4000:
            continue

        askPrice = Decimal(s['askPrice'])
        bidPrice = Decimal(s['bidPrice'])

        spread = calculate_spread_percentage(bidPrice, askPrice, get_price(pair))

        if spread > maxSpread:
            maxSpread = spread
            bestPair = pair

    #bestSymData = get_symbol_data(bestPair)
    return bestPair, round(maxSpread,2) #Symbol(bestSymData)




"""
poop = get_recent_trades("BATETH")
poop = poop[::-1]
print(poop)

for p in poop:
    print(p)
    """