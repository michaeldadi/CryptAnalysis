class Strategies:

    @staticmethod
    def maStrategy(df, i):
        # Return true if price is 10% below SMA
        buy_price = 0.96 * df['slow_sma'][i]
        if buy_price >= df['close'][i]:
            return min(buy_price, df['high'][i])

        return False

    @staticmethod
    def bollStrategy(df, i):
        # Return true if price is 2.5% lower than LBB
        buy_price = 0.975 * df['low_boll'][i]
        if buy_price >= df['close'][i]:
            return min(buy_price, df['high'][i])

        return False
