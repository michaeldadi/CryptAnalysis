import decimal
import hashlib
import hmac
import json
import time

import pandas as pd
import requests

import config

binance_keys = {
    'api_key': config.api_key,
    'secret_key': config.api_secret
}


class Binance:
    def __init__(self):
        self.base = 'https://api.binance.us'

        self.endpoints = {
            "order": '/api/v3/order',
            "testOrder": '/api/v3/order/test',
            "allOrders": '/api/v3/allOrders',
            "klines": '/api/v3/klines',
            "exchangeInfo": '/api/v3/exchangeInfo'
        }

        self.headers = {"X-MBX-APIKEY": binance_keys['api_key']}

    def GetTradingSymbols(self, quoteAssets=None):
        # Get all tradable symbols
        url = self.base + self.endpoints["exchangeInfo"]

        try:
            response = requests.get(url)
            data = json.loads(response.text)
        except Exception as e:
            print("Exception occurred attempting to access " + url)
            print(e)
            return []

        symbols_list = []

        for pair in data['symbols']:
            if pair['status'] == 'TRADING':
                if quoteAssets is not None and pair['quoteAsset'] in quoteAssets:
                    symbols_list.append(pair['symbol'])

        return symbols_list

    def GetSymbolData(self, symbol, interval):
        # Get trading data for one symbol
        params = '?&symbol=' + symbol + '&interval=' + interval

        url = self.base + self.endpoints['klines'] + params

        # Download data
        data = requests.get(url)
        dictionary = json.loads(data.text)

        # Dataframe and cleanup
        df = pd.DataFrame.from_dict(dictionary)
        df = df.drop(range(6, 12), axis=1)

        # Rename cols
        col_names = ['time', 'open', 'high', 'low', 'close', 'volume']
        df.columns = col_names

        # Change values from str to float
        for col in col_names:
            df[col] = df[col].astype(float)

        df['date'] = pd.to_datetime(df['time'] * 1000000, infer_datetime_format=True)

        return df

    def PlaceOrder(self, symbol, side, type, quantity, price, test=True):
        params = {
            'symbol': symbol,
            'side': side,
            'type': type,
            'timeInForce': 'GTC',
            'quantity': quantity,
            'price': self.floatToString(price),
            'recvWindow': 5000,
            'timestamp': int(round(time.time() * 1000))
        }

        if type != 'MARKET':
            params['timeInForce'] = 'GTC'
            params['price'] = self.floatToString(price)

        self.signRequest(params)

        url = ''
        if test:
            url = self.base + self.endpoints['testOrder']
        else:
            url = self.base + self.endpoints['order']

        try:
            response = requests.post(url, params=params, headers=self.headers)
            data = response.text
        except Exception as e:
            print("Exception occurred attempting to place order on " + url)
            print(e)
            data = {'code': '-1', 'msg': e}

        return json.loads(data)

    def CancelOrder(self, symbol, orderId):
        params = {
            'symbol': symbol,
            'orderId': orderId,
            'recvWindow': 5000,
            'timestamp': int(round(time.time() * 1000))
        }

        self.signRequest(params)

        url = self.base + self.endpoints['order']

        try:
            response = requests.delete(url, params=params, headers=self.headers)
            data = response.text
        except Exception as e:
            print("Exception occurred attempting to cancel order on " + url)
            print(e)
            data = {'code': '-1', 'msg': e}

        return json.loads(data)

    def GetOrderInfo(self, symbol, orderId):
        params = {
            'symbol': symbol,
            'orderId': orderId,
            'recvWindow': 5000,
            'timestamp': int(round(time.time() * 1000))
        }

        self.signRequest(params)

        url = self.base + self.endpoints['order']

        try:
            response = requests.get(url, params=params, headers=self.headers)
            data = response.text
        except Exception as e:
            print("Exception occurred attempting to get order info on " + url)
            print(e)
            data = {'code': '-1', 'msg': e}

        return json.loads(data)

    def GetAllOrderInfo(self, symbol):
        params = {
            'symbol': symbol,
            'timestamp': int(round(time.time() * 1000))
        }

        self.signRequest(params)

        url = self.base + self.endpoints['allOrders']

        try:
            response = requests.get(url, params=params, headers=self.headers)
            data = response.text
        except Exception as e:
            print("Exception occurred attempting to get info on all orders on " + url)
            print(e)
            data = {'code': '-1', 'msg': e}

        return json.loads(data)

    def floatToString(self, f):
        context = decimal.Context()
        context.prec = 12
        d1 = context.create_decimal(repr(f))
        return format(d1, 'f')

    def signRequest(self, params: dict):
        query_str = '&'.join(["{}={}".format(d, params[d]) for d in params])
        signature = hmac.new(binance_keys['secret_key'].encode('utf-8'), query_str.encode('utf-8'), hashlib.sha256)
        params['signature'] = signature.hexdigest()
