from decimal import Decimal, getcontext


class StrategyEvaluator:
    def __init__(self, strategy_func, strategy_settings: dict = {'indicators': ['low_boll', 'fast_sma', 'slow_sma']}):
        self.strategy = strategy_func
        self.settings = strategy_settings
        self.buy_times = []
        self.sell_times = []

        self.profitable_symbols = 0
        self.unprofitable_symbols = 0

        self.complete_start_bal = 0
        self.complete_result_bal = 0

        self.profit_list = []
        self.results = dict()

    def backTest(self,
                 model,
                 start_bal=100,
                 initial_profit=1.045,
                 initial_stop_loss=0.85,
                 incremental_profit=1.04,
                 incremental_stop_loss=0.975):

        if initial_stop_loss >= 1 or initial_stop_loss <= 0:
            AssertionError("initial_stop_loss should be between 0 and 1!")

        if initial_profit <= 1:
            AssertionError("initial_profits should be greater than 1!")

        df = model.df
        buy_times = []
        sell_times = []

        last_buy = None

        getcontext().prec = 30

        resulting_bal = Decimal(start_bal)
        stop_loss = Decimal(initial_stop_loss)
        profit_target = Decimal(initial_profit)
        buy_price = 0

        # Go through all candlesticks
        for i in range(0, len(df['close']) - 1):
            if last_buy is None:
                strategy_result = self.strategy(model.df, i)

                if strategy_result:
                    buy_price = Decimal(strategy_result)
                    last_buy = {
                        "index": i,
                        "price": buy_price
                    }
                    buy_times.append([df['time'][i], buy_price])

                    stop_loss = Decimal(initial_stop_loss)
                    profit_target = Decimal(initial_profit)

            elif last_buy is not None and i > last_buy["index"] + 1:
                stop_loss_price = last_buy["price"] * stop_loss
                next_target_price = last_buy["price"] * profit_target

                if df['low'][i] < stop_loss_price:
                    sell_times.append([df['time'][i], stop_loss_price])
                    resulting_bal *= (stop_loss_price / buy_price)

                    last_buy = None
                    buy_price = Decimal(0)

                elif df['high'][i] > next_target_price:
                    last_buy = {
                        "index": i,
                        "price": Decimal(next_target_price)
                    }

                    stop_loss = Decimal(incremental_stop_loss)
                    profit_target = Decimal(incremental_profit)

        self.results[model.symbol] = dict(
            returns=round(Decimal(100.0) * (resulting_bal / Decimal(start_bal) - Decimal(1.0)), 3),
            buy_times=buy_times,
            sell_times=sell_times
        )

        if resulting_bal > start_bal:
            self.profitable_symbols += 1
        elif resulting_bal < start_bal:
            self.unprofitable_symbols += 1

        return resulting_bal

    def evaluate(self, model):
        last_entry = len(model.df['close']) - 1
        return self.strategy(model.df, last_entry)

    def updateResult(self, start_bal, resulting_bal):
        self.complete_start_bal += start_bal
        self.complete_result_bal += resulting_bal

    def printResults(self):
        print(self.strategy.__name__ + "STATS: ")
        print("Profitable Symbols: " + str(self.profitable_symbols))
        print("Unprofitable Symbols: " + str(self.unprofitable_symbols))

        if len(self.profit_list) > 0:
            profitability = Decimal(100.0) * (self.complete_result_bal / self.complete_start_bal - Decimal(1.0))
            print("Overall Profits: " + str(round(sum(self.profit_list), 2)))
            print("Least Profitable Trade: " + str(round(min(self.profit_list), 2)))
            print("Most Profitable Trade: " + str(round(max(self.profit_list), 2)))
            print("With an initial balance of " + str(round(self.complete_start_bal))
                  + " and a final balance of " + str(round(self.complete_result_bal, 2)))
            print("The profitability is " + str(round(profitability, 2)) + "%")
