#!/usr/bin/python3
import lib
import secret
import time
from poloniex import Poloniex
p = Poloniex(*secret.token_old)

margin = 0.013
min = 10015

while True:
    all_prices = lib.returnTicker(forceUpdate = True)
    all_trades = lib.tradeHistory('all', forceUpdate=True)
    cur_balances = {k: v for k, v in lib.returnCompleteBalances().items() if v['btcValue'] > 0.00001}
    positive_balances = {k: v['cur'] for k,v in cur_balances.items() }

    tcount = 0
    for k, v in positive_balances.items():
        if k == 'BTC':
            continue

        exchange = "BTC_{}".format(k)
        last_trade = all_trades[exchange][-1]
        last_rate = last_trade['rate']
        current = all_prices[exchange]

        if last_rate * (1 + margin) < current['highestBid']:
            amount_to_trade = min / int(current['highestBid_orig'].lstrip("0."))
            try:
                res = p.sell(currencyPair=exchange, rate=current['highestBid_orig'], amount=amount_to_trade, orderType="fillOrKill")
                print("SELL {:9} {:.8f} {:.8f}".format(exchange, current['highestBid'], last_rate))
            except:
                print("FAILED SELL {:9} {:.8f} {:.8f}".format(exchange, current['highestBid'], last_rate))
                pass
            tcount += 1

        elif last_rate * (1 - margin) > current['lowestAsk']:
            amount_to_trade = min / int(current['lowestAsk_orig'].lstrip("0."))
            try:
                res = p.buy(currencyPair=exchange, rate=current['lowestAsk_orig'], amount=amount_to_trade, orderType="fillOrKill")
                print("BUY  {:9} {:.8f} {:.8f}".format(exchange, current['lowestAsk'], last_rate))
            except:
                print("FAILED BUY  {:9} {:.8f} {:.8f}".format(exchange, current['lowestAsk'], last_rate))
                pass
            tcount += 1

    if tcount == 0:
        print("no trades")

    print("----------------")

    time.sleep(120)
