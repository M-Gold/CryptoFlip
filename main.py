import Binance
import json, time, sys, os.path, configparser
from decimal import *

totalProfit = Decimal(0)
myEth = Decimal(.05)
loops = 0
while True:
    pair, _ = Binance.get_best_spread("ETH")
    print(pair)

    bidOrder = Binance.create_bid_order(pair, myEth)
    bidOrder.prepare_sim()
    bidOrder.place()
    completed = False
    while not completed:
        completed = bidOrder.update()
        time.sleep(2)

    bought = bidOrder.quantBoughtTotal
    spent = bidOrder.amountSpent
    #myEth -= spent
    print("\n----------------------------------------------")
    print("Completed buying. Bought: {} {}".format(bought, bidOrder.sym.minorSymbol))
    print("----------------------------------------------\n")


    askOrder = Binance.create_ask_order(pair, bought)
    askOrder.prepare_sim()
    askOrder.place()
    completed = False

    while not completed:
        completed = askOrder.update()
        time.sleep(2)




    earned = askOrder.amountEarned
    #myEth += earned
    sold = askOrder.quantSoldTotal

    profit = earned - spent
    profit -= profit * Decimal(.005)
    myEth += profit
    totalProfit += profit
    loops += 1
    print("\n><><><><><><><><><><><><><><")
    print("DONE!!!!!")
    print("Spent {} ETH FOR {} {}".format(spent, bought, askOrder.sym.minorSymbol))
    print("Earned {} ETH SELLING {} {}".format(earned, sold, askOrder.sym.minorSymbol))
    print("Profit: {}".format(earned - spent))
    print("Loops: {} TotalEth: {}".format(loops, myEth))
    print("><><><><><><><><><><><><><><\n")













exit()
MIN_SPREAD_PERCENT = 1.5

bestSpreadPercent = 0

while bestSpreadPercent < MIN_SPREAD_PERCENT:

    time.sleep(5)
    bestPair, bestSpreadPercent = Binance.get_best_spread("ETH")
    print("{}: {}".format(bestPair, bestSpreadPercent))



print("Best pair is: {}".format(bestPair))
print("Creating bid order for {} of .05 ETH".format(bestPair))
order = Binance.create_bid_order(bestPair, .05)
order.prepare()



#order.place()


"""
Need some kind of Order object from Binance

It needs basic opertations

Order.Status()
Order.Prepare()
Order.Place()
Order.Abort() --returns total
Order.Improve()

And some info

Order.TotalBought

Order.Profit
Order.AvgBidIncrease
Order.AvgAskDecrease




Then some higher Operation

--PRepare order
--place order

--watch order
--watch market

--abort order if spread shrinks
--improve order if outbid
--flip from buying to selling






"""








