import pandas as pd
import requests
import json

import plotly.graph_objs as go
from plotly.offline import plot

from pyti.smoothed_moving_average import smoothed_moving_average as sma


class TradingModel:

    def __init__(self, symbol):
        self.symbol = symbol
        self.df = self.getData()

    def getData(self):
        # Define
        base = 'https://api.binance.com'
        endpoint = '/api/v1/klines'
        params = '?&symbol=' + self.symbol + '&interval=1h'

        url = base + endpoint + params

        # Download
        data = requests.get(url)
        dictionary = json.loads(data.text)

        # Dataframe and cleanup
        df = pd.DataFrame.from_dict(dictionary)
        df = df.drop(range(6, 12), axis=1)

        # Rename columns
        col_names = ['time', 'open', 'high', 'low', 'close', 'volume']
        df.columns = col_names

        # Change values from str to float
        for col in col_names:
            df[col] = df[col].astype(float)

        # Add moving averages
        df['fast_sma'] = sma(df['close'].tolist(), 10)
        df['slow_sma'] = sma(df['close'].tolist(), 30)

        return df

    def strategy(self):
        df = self.df
        buy_signals = []
        # If price is 3% below SMA, buy
        # If price is 2% above buying price, sell
        for i in range(1, len(df['close'])):
            if df['slow_sma'][i] > df['low'][i] and (df['slow_sma'][i] - df['low'][i]) > 0.03 * df['low'][i]:
                buy_signals.append([df['time'][i], df['low'][i]])

        self.plotData(buy_signals=buy_signals)

    def plotData(self, buy_signals=False):
        df = self.df
        # Plot candlestick chart
        candle = go.Candlestick(
            x=df['time'],
            open=df['open'],
            close=df['close'],
            high=df['high'],
            low=df['low'],
            name="Candlesticks")

        # Plot MAs
        fsma = go.Scatter(
            x=df['time'],
            y=df['fast_sma'],
            name="Fast SMA",
            line=dict(color='rgba(102, 207, 255, 50)'))

        ssma = go.Scatter(
            x=df['time'],
            y=df['slow_sma'],
            name="Slow SMA",
            line=dict(color='rgba(255, 207, 102, 50)'))

        data = [candle, ssma, fsma]

        if buy_signals:
            buys = go.Scatter(
                x=[item[0] for item in buy_signals],
                y=[item[1] for item in buy_signals],
                name="Buy Signals",
                mode="markers")

            sells = go.Scatter(
                x=[item[0] for item in buy_signals],
                y=[item[1] * 1.02 for item in buy_signals],
                name="Sell Signals",
                mode="markers")

            data = [candle, ssma, fsma, buys, sells]

        # Style and UI
        layout = go.Layout(title=self.symbol)
        fig = go.Figure(data=data, layout=layout)

        plot(fig, filename=self.symbol)


def Main():
    symbol = "BTCUSDT"
    model = TradingModel(symbol)
    model.strategy()


if __name__ == '__main__':
    Main()
