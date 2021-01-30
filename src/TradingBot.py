from decimal import Decimal

from Binance import Binance
from Strategies import Strategies
from StrategyEvaluator import StrategyEvaluator
from TradingModel import TradingModel


def BackTestStrategies(symbols=[], interval='4h', plot=False):
    trade_value = Decimal(100)

    strategy_evaluators = [
        StrategyEvaluator(strategy_func=Strategies.bollStrategy, strategy_settings={'indicators': ['low_boll']}),
        StrategyEvaluator(strategy_func=Strategies.maStrategy, strategy_settings={'indicators': ['slow_sma']})
    ]

    coins_tested = 0

    for symbol in symbols:
        print(symbol)

        model = TradingModel(symbol=symbol, timeframe=interval)

        for evaluator in strategy_evaluators:
            result_bal = evaluator.backTest(
                model,
                start_bal=trade_value
            )

            if result_bal != trade_value:
                print(evaluator.strategy.__name__
                      + ": starting balance: " + str(trade_value)
                      + ": resulting balance: " + str(round(result_bal, 2)))

                if plot:
                    model.plotData(
                        buy_signals=evaluator.results[model.symbol]['buy_times'],
                        sell_signals=evaluator.results[model.symbol]['sell_times'],
                        plot_title=evaluator.strategy.__name__ + " on " + model.symbol,
                        indicators=evaluator.settings['indicators'])

                evaluator.profit_list.append(result_bal - trade_value)
                evaluator.updateResult(trade_value, result_bal)

            coins_tested += 1

    for evaluator in strategy_evaluators:
        print("")
        evaluator.printResults()


def Main():
    exchange = Binance()
    symbols = exchange.GetTradingSymbols(quoteAssets=["BTC", "USDT"])

    BackTestStrategies(symbols=symbols, interval='5m', plot=True)


if __name__ == '__main__':
    Main()
