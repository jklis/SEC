import csv
from netIncome import get_past_net_income
from yahoo import TickerValues

def get_ticker_list(file, ticker_column, price_column, has_header=True):
    tickers = []
    prices = []
    with open(file) as csvfile:
        ticker_reader = csv.reader(csvfile, delimiter=',')
        if has_header:
            ticker_reader = iter(ticker_reader)
            next(ticker_reader)

        for row in ticker_reader:
            tickers.append(row[ticker_column])
            prices.append(row[price_column])
    return tickers, prices


tickers, prices = get_ticker_list("companylist.csv", 0, 2)
net_incomes = []
for ticker in tickers:
    tick_value = TickerValues(ticker)
    tick_value.update_all_values()
    income = tick_value.net_income
    print(income)
    net_incomes.append(income)
for income in net_incomes:
    print(income)
