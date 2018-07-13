
# Information Needed:
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

import requests
from bs4 import BeautifulSoup as BS


class TickerValues:
    def __init__(self, ticker):
        self.net_income = {}
        self.total_assets = {}
        self.total_cash_flow = {}
        self.long_term_debt = {}
        self.common_stock_equity = {}
        self.preferred_stock_equity = {}
        self.total_liabilities = {}
        self.sale_purchase_stock = {}
        self.gross_profit = {}
        self.total_revenue = {}
        self.ticker = ticker

    def update_all_values(self):
        income, balance, cash, years = self.get_tables()
        self.net_income = self.get_value(income, years, "Net Income")
        self.total_assets = self.get_value(balance, years, "Total Current Assets")
        self.total_cash_flow = self.get_value(cash, years, "Total Cash Flow From Operating Activities")
        self.long_term_debt = self.get_value(balance, years, "Long Term Debt")
        self.common_stock_equity = self.get_value(balance, years, "Common Stock")
        self.preferred_stock_equity = self.get_value(balance, years, "Preferred Stock")
        self.total_liabilities = self.get_value(balance, years, "Total Liabilities")
        self.sale_purchase_stock = self.get_value(cash, years, "Sale Purchase of Stock")
        self.gross_profit = self.get_value(income, years, "Gross Profit")
        self.total_revenue = self.get_value(income, years, "Total Revenue")

    def get_value(self, doc, years, value):
        output = {}
        for year in years:
            key = (value, year)
            output[year] = doc[key]
        return output

    def get_tables(self):
        income_statement_url = "/financials?p="
        balance_sheet_url = "/balance-sheet?p="
        cash_flow_url = "/cash-flow?p="
        income_statement_soup = self.get_soup(income_statement_url)
        balance_sheet_soup = self.get_soup(balance_sheet_url)
        cash_flow_soup = self.get_soup(cash_flow_url)
        income_statement_table = income_statement_soup.find('table')
        income_statement, years = self.parse_soup_table(income_statement_table)
        cash_flow_table = cash_flow_soup.find('table')
        cash_flow, years = self.parse_soup_table(cash_flow_table)
        balance_sheet_table = balance_sheet_soup.find('table')
        balance_sheet, years = self.parse_soup_table(balance_sheet_table)
        return income_statement, balance_sheet, cash_flow, years

    def get_soup(self, tab_url):
        base_url = "https://finance.yahoo.com/quote/"
        url = base_url + self.ticker + tab_url + self.ticker
        res = requests.get(url)
        soup = BS(res.content, 'lxml')
        return soup

    def parse_soup_table(self, table):
        rows = table.find_all('tr')
        header = 0
        years = []
        output = {}
        for row in rows:
            columns = row.find_all('td')
            if header == 0:
                col = iter(columns)
                next(col)
                for column in col:
                    years.append(column.get_text())
                header += 1
            elif len(columns) > 1:
                index = 0
                row_key = ""
                for column in columns:
                    if index == 0:
                        row_key = column.get_text()
                    else:
                        output[(row_key, years[index - 1])] = column.get_text()
                    index += 1
        return output, years


aapl = TickerValues("aapl")
aapl.update_all_values()
print(aapl.net_income)
