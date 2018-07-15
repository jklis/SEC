import csv
from yahoo import TickerValues

# Net Income
# Total Assets
# Total Cash flow from operating activities
# Long-term debt
# Common Stock Equity
# Preferred Stock Equity
# Total Liabilities
# Sale Purchase of stock
# Gross Profit
# Total Revenue


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


file_name = "output.csv"
file = open(file_name, 'w')
file_header = "Ticker,Year,Net Income,Total Assets,Total Cash Flow,Long-term Debt,Common Stock Equity,Preferred Stock Equity,Total Liabilities,Sale Purchase of Stock,Gross Profit,Total Revenue\n"
file.write(file_header)

file.close()
tickers, prices = get_ticker_list("companylist.csv", 0, 2)
with open(file_name, 'a') as file:
    for ticker in tickers:
        print(ticker)
        tick_value = TickerValues(ticker)
        tick_value.update_all_values()
        income = tick_value.net_income
        total_assets = tick_value.total_assets
        total_cash = tick_value.total_cash_flow
        long_term_debt = tick_value.long_term_debt
        common_stock = tick_value.common_stock_equity
        preferred_stock = tick_value.preferred_stock_equity
        total_liabilities = tick_value.total_liabilities
        sale_purchase = tick_value.sale_purchase_stock
        gross_profit = tick_value.gross_profit
        total_revenue = tick_value.total_revenue
        years = income.keys()
        for year in years:
            data = str.format("{},{},{},{},{},{},{},{},{},{},{},{}",ticker, year, income[year], total_assets[year],
                              total_cash[year], long_term_debt[year], common_stock[year], preferred_stock[year],
                              total_liabilities[year], sale_purchase[year], gross_profit[year], total_revenue[year])
            file.write(data)