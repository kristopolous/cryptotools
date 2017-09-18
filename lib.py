#!/usr/bin/python3
import os
import time
import urllib.request
import json
import secret
import math
import re
import sys
from datetime import datetime
from operator import itemgetter, attrgetter

one_day = 86400

polo_instance = False

def bprint(what):
    # there's probably smarter ways to do this ... but
    # I can't think of one
    for i in range(6, 0, -1):
        what = re.sub('^0\.{}'.format('0' * i), '_.{}'.format('_' * i), what)
        what = re.sub(' 0\.{}'.format('0' * i), ' _.{}'.format('_' * i), what)

    what = re.sub('^0\.', '_.', what)
    what = re.sub(' 0\.', ' _.', what)
    
    print(what)

def polo_connect():
    global polo_instance
    if not polo_instance:
        import secret
        from poloniex import Poloniex
        polo_instance = Poloniex(*secret.token)
    return polo_instance

def need_to_get(path, doesExpire = True, expiry = one_day / 2):
    now = time.time()

    if not os.path.isfile(path) or os.path.getsize(path) < 10:
        return True

    if doesExpire:
        return now > (os.stat(path).st_mtime + expiry)

def cache_get(fn, expiry=300):
    name = "cache/{}".format(fn)
    if need_to_get(name, expiry=expiry):
        with open(name, 'w') as cache:
            p = polo_connect() 
            data = getattr(p, fn)()
            json.dump(data, cache)

    with open(name) as handle:
        data = handle.read()
        if len(data) > 10:
            return json.loads(data)

def returnOpenOrders():
    return cache_get('returnOpenOrders', expiry=30)

def returnCompleteBalances():
    return cache_get('returnCompleteBalances')

def btc_price():
    if need_to_get('cache/btc'):
        with open('cache/btc', 'wb') as cache:
            cache.write(urllib.request.urlopen("https://api.coindesk.com/v1/bpi/currentprice.json").read())

    with open('cache/btc') as json_data:
        d = json.load(json_data)
        return d['bpi']['USD']['rate_float']


def ignorePriorExits(tradeList):
    ttl_btc = 0
    ttl_cur = 0
    recent = []

    for row in tradeList:
        if row['type'] == 'buy':
            ttl_cur += row['cur']
        if row['type'] == 'sell':
            ttl_cur -= row['cur']

        # if we've exited the currency then we reset our
        # counters
        if ttl_cur < 0.0000000001:
            recent = []
        else:
            recent.append(row)

    return recent


def ticker():
    with open('cache/ticker') as json_data:
        d = json.load(json_data)
        return d

def to_float(tradeList):
    for i in range(0, len(tradeList)):
        for term in  ['total', 'amount', 'rate', 'fee']:
            tradeList[i][term] = float(tradeList[i][term])

        tradeList[i]['btc'] = tradeList[i]['total']
        tradeList[i]['cur'] = tradeList[i]['amount']

        if tradeList[i]['type'] == 'sell':
            tradeList[i]['btc'] -= tradeList[i]['total'] * tradeList[i]['fee']

        if tradeList[i]['type'] == 'buy':
            tradeList[i]['cur'] -= tradeList[i]['cur'] * tradeList[i]['fee']

        tradeList[i]['date'] = datetime.strptime( tradeList[i]['date'], '%Y-%m-%d %H:%M:%S' )

    return tradeList

def trade_history(currency = 'all'):
    if currency != 'all':
        all_trades = trade_history()
        return all_trades[currency]

    step = one_day * 7
    now = time.time()
    start = 1501209600
    doesExpire = False
    all_trades = []
    for i in range(start, int(now), step):
        if now - i < step:
            doesExpire = True

        name = 'cache/{}-{}.txt'.format(currency, i)
        if need_to_get(name, doesExpire = doesExpire, expiry = 300):
            with open(name, 'w') as cache:
                p = polo_connect() 
                end = i + step
                if end > now:
                    end = False
                history = p.returnTradeHistory(currencyPair=currency, start=i, end=end)
                json.dump(history, cache)

        with open(name) as handle:
            data = handle.read()
            if len(data) > 10:
                json_data = json.loads(data)
                if isinstance(json_data, dict):
                    if not isinstance(all_trades, dict):
                        all_trades = {}

                    for k,v in json_data.items():
                        if k not in all_trades:
                            all_trades[k] = []
                        all_trades[k] += v
                else:
                    all_trades += json_data

    for k,v in all_trades.items():
        all_trades[k] = sorted(to_float(v), key=itemgetter('date'))

    return all_trades
