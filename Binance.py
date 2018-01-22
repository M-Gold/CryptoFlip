from binance.client import Client
from binance.enums import *
from decimal import *
import json, time


CACHE_LIFESPAN = 10# seconds
TRADE_TAX = .001 #Binance's .1% fee


#---- Binance API information
api_key = ""
api_secret = ""

client = Client(api_key, api_secret)


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

    dayTickerData = None
    lastDayTickerUpdate = 0




 #--------------------Orders

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



#----------------Market Info Functions
def get_orderbook_tickers():
    if time.time() - DataCache.lastOrderBookUpdate >= CACHE_LIFESPAN:
        #fetch new
        print("GETTING FRESH ORDERBOOK")
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
        print("GETTING FRESH 24HR")
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
        print("GETTING FRESH SYMBOL DATA")
        info = client.get_symbol_info(symbol)
        DataCache.symbolInfo[symbol] = info
        DataCache.lastSymbolUpdate[symbol] = time.time()
    else:
        info = DataCache.symbolInfo[symbol]

    return info

def get_pair_volume(pair):
    ticker = get_24hr_ticker()

    for p in ticker:
        if p['symbol'] == pair:
            return Decimal(p['quoteVolume'])

def get_price(pair):

    if time.time() - DataCache.lastPriceUpdate >= CACHE_LIFESPAN:
        #fetch new
        print("FETCHING NEW PRICE")
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
        print(step)


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
        return self.buy(quantity, price)

    def sell(self, quantity, price):
        return order_sell(self.pairSymbol, quantity, price)

    def sell_max(self, price):
        balance = self.get_balance()
        quantity = self.get_max_sellable_quant(balance)
        return self.sell(quantity, price)

    def abort_order(self, orderId):
        return order_abort(self.pairSymbol, orderId)

    def order_status(self, orderId):
        return order_status(self.pairSymbol, orderId)

    def get_volume(self):
        return get_pair_volume(self.pairSymbol)



def get_best_spread(symbol):

    tickers = get_orderbook_tickers()

    data = json.dumps(tickers)
    data = json.loads(data)

    maxSpread = 0
    bestPair = ""
    bestAskPrice = 0
    bestBidPrice = 0
    for s in data:
        pair = s['symbol']
        if symbol not in pair:
            continue
        if "USDT" in pair:
            continue

        if get_pair_volume(pair) < 2000:
            continue

        askPrice = Decimal(s['askPrice'])
        bidPrice = Decimal(s['bidPrice'])

        spread = calculate_spread_percentage(bidPrice, askPrice, get_price(pair))

        if spread > maxSpread:
            maxSpread = spread
            bestPair = pair

    bestSymData = get_symbol_data(bestPair)
    return Symbol(bestSymData)