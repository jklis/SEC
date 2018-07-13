

# F-Score Calculation from https://en.wikipedia.org/wiki/Piotroski_F-Score
# 1. Return on Assets (1 point if it is positive in the current year)
# 2. Operating cash flow (1 point if it is positive in the current year)
# 3. Change in Return on Assets (1 point if ROA is higher in the current year compared ot the previous one)
# 4. Accruals (1 point if Operating cash flow/total assets is higher than ROA in the current year)
# 5. Change in leverage (long-term) ratio (1 point if the ratio is lower this year compared ot the previous one)
# 6. Change in current ratio (1 point if it is higher in the current year compared to the previous one)
# 7. Change in the number of shares (1 point if no new shares were issued during the last year)
# 8. Change in gross margin (1 point if it is higher in the current year compared to the previous one)
# 9. Change in asset turnover ratio (1 point if it is higher in the current year compared to the previous one)

# 1. Return on Assets
# +1 ROA = Net Income / Total Assets is positive
#
# 2. Operating cash flow
# +1 if Total Cash flow from operating activities is positive
#
# 3. Change in Return on Assets
#  +1 if ROA This Year > ROA Last Year
#
# 4. Accruals
# +1 if ( Operating Cash Flow ) / ( Total Assets ) > ROA
#
# 5. Long-term debt to equity ratio
# +1 if ( Long-term debt ) / ( Common Stock + Preferred Stock ) < previous years
#
# 6. Current Ratio
# +1 if ( Total Assets ) / ( Total Liabilities ) > previous years
#
# 7. Change in Shares
# +1 if sale purchase of stock is <= 0
#
# 8. Change in gross margin
# +1 if ( Gross Profit ) / ( Total Revenue ) > previous years
#
# 9. Change in asset turnover ratio
# +1 if ( Ending Assets Previous year + Ending Assets this year ) / ( 2 * Total Revenue ) > previous years
#
#
# Information Needed:
# Net Income
# Total Assets
# Total Cash flow from operating activities
# Operating Cash Flow
# Total Assets
# Long-term debt
# Common Stock Equity
# Preferred Stock Equity
# Total Liabilities
# Sale Purchase of stock
# Gross Profit
# Total Revenue

import re
import requests
from bs4 import BeautifulSoup
import datetime
from dateutil.parser import parse


base_link = "https://www.sec.gov"
this_year = 2018

def get_links(ticker, file_type):
    base_url1 = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK="
    base_url2 = "&type="
    base_url3 = "&dateb=&owner=exclude&count=40"

    url = base_url1 + ticker + base_url2 + file_type + base_url3
    res = requests.get(url)
    soup = BeautifulSoup(res.content, 'lxml')
    filings = soup.find_all(id="documentsbutton")
    dates = []
    for filing in filings:
        date_string = filing.parent.next_sibling.next_sibling.next_sibling.next_sibling.string
        match = re.search(r'\d{4}-\d{2}-\d{2}', date_string)
        date = datetime.datetime.strptime(match.group(), '%Y-%m-%d').date()
        dates.append(date)

    links = []
    for link in filings:
        links.append(base_link + link.get('href'))

    index = 0
    good_links = []
    link_years = []
    for date in dates:
        if date > datetime.datetime(2008, 1, 1).date():
            if not is_ammend(soup, index):
                link_years.append(date.year)
                good_links.append(links[index])
            index += 1

    return good_links, link_years


def is_ammend(page, index):
    table = page.find(class_="tableFile2")
    rows = table.find_all('tr')
    index += 1
    row = rows[index]
    filing = row.find('td').get_text()
    if "A" in filing:
        return True
    return False


def is_valid_year(num):
    return (this_year - 10) <= num < this_year


def get_document(link):
    res = requests.get(link)
    soup = BeautifulSoup(res.content, 'lxml')
    table = soup.select('table[summary="Document Format Files"]')
    doc_link = table[0].find('a').get('href')
    res = requests.get(base_link + doc_link)
    return res.content


def get_all_net_incomes(tables):
    try:
        income_table, income_cell = find_net_income(tables)
        if income_table is None or income_cell is None:
            return None
        years = get_all_income_years(income_table)
        skip_tables = []
        skip_tables.append(income_table)
        while years is None or len(years) is 0:
            income_table, income_cell = find_net_income(tables, skip_tables)
            skip_tables.append(income_table)
            years = get_all_income_years(income_table)
            if len(skip_tables) == len(tables):
                return None
        net_incomes = get_net_incomes(income_cell)
        if len(years) != len(net_incomes):
            if len(years) * 4 == len(net_incomes):
                new_net_incomes = []
                index = 0
                next_income = 0
                for income in net_incomes:
                    next_income += income
                    index += 1
                    if index == 4:
                        new_net_incomes.append(next_income)
                        next_income = 0
                        index = 0
                net_incomes = new_net_incomes
            elif len(years) > 0 and len(net_incomes) > 0:
                temp_years = []
                temp_incomes = []
                for year, income in zip(years, net_incomes):
                    temp_years.append(year)
                    temp_incomes.append(income)
                years = temp_years
                net_incomes = temp_incomes
            else:
                return None
        return years, net_incomes
    except TypeError:
        return None


def find_net_income(tables, skip=[]):
    try:
        for table in tables:
            if table not in skip:
                cells = table.find_all('td')
                for cell in cells:
                    text = get_cell_text(cell)
                    if text == "Net income" or text == "Net income (loss)" or text == "Net earnings" or text == "Net loss" or text == "Net (loss) income" or "Net decrease in net assets resulting from operations":
                        return table, cell
    except TypeError:
        return None
    return None


def get_all_income_years(table):
    years = []
    rows = table.find_all('tr')
    found_year_row = False
    for row in rows:
        if found_year_row:
            return years
        columns = row.find_all('td')
        for column in columns:
            text = get_cell_text(column)
            text = text.split('(')
            text = text[0]
            text = get_useable_text(text)
            if text.isdigit():
                if is_valid_year(int(text)):
                    found_year_row = True
                    years.append(int(text))
            elif is_date(text):
                try:
                    text = text.replace(',', ', ')
                    date = parse(text)
                    year = date.year
                    if is_valid_year(year):
                        found_year_row = True
                        years.append(year)
                except ValueError:
                    break
    return years


def get_net_incomes(cell):
    row = cell.parent
    while row.name != "tr":
        row = row.parent
    columns = row.find_all('td')
    incomes = []
    for column in columns:
        text = column.get_text()
        text = text.replace(',', '')
        text = text.replace('\n', '')
        is_loss = 1
        if len(text) > 0:
            if text[0] == "(":
                is_loss = -1
            text = text.replace('(', '')
            text = text.replace(')', '')
            text = text.strip()
            if text.isdigit():
                income = int(text) * is_loss
                incomes.append(income)
    return incomes


def find_column_num(year, table):
    rows = table.find_all('tr')
    for row in rows:
        columns = row.find_all('td')
        column_num = 0
        for column in columns:
            text = get_cell_text(column)
            text = get_useable_text(text)
            if text.isdigit():
                if int(text) == year:
                    return column_num
                column_num += 1


def get_cell_text(cell):
    try:
        text = cell.get_text()
        if (text is None or len(text) is 0) and len(cell.contents) > 0:
            text = cell.contents[0].get_text()
        text = text.replace('\n', '')
        #text = text.split('(')
        #text = text[0]
        text = text.strip()
        return text
    except AttributeError:
        return ""


def get_useable_text(text):
    text = text.split('(')
    text = text[0]
    return text


def get_n_num(n, base_cell):
    row = base_cell.parent
    while row.name != "tr":
        row = row.parent
    columns = row.find_all('td')
    index = 0
    for column in columns:
        text = column.get_text()
        text = text.replace(',', '')
        text = text.replace('\n', '')
        if text.isdigit():
            if index == n:
                num = int(text)
                return num
            index += 1


def is_date(string):
    try:
        parse(string)
        return True
    except ValueError:
        return False


def find_doc_year(doc):
    header_divs = doc.find_all("div", class_="infoHead")
    for div in header_divs:
        if div.get_text() == "Period of Report":
            date_text = div.next_sibling.get_text()


def get_past_net_income(ticker, num_years=1):
    try:
        links, years = get_links(ticker, "10-k")
        incomes = dict()
        if years[0] == this_year:
            index = 0
            for year in years:
                year -= 1
                years[index] = year
                index += 1

        for link in links:
            filing_doc = get_document(link)
            doc_soup = BeautifulSoup(filing_doc, 'lxml')
            tables = doc_soup.find_all('table')
            if tables is None:
                return None
            temp_dict = dict()
            years, net_incomes = get_all_net_incomes(tables)
            if years is None or net_incomes is None:
                return None
            for year, income in zip(years, net_incomes):
                temp_dict[year] = income
            keylist = temp_dict.keys()
            for key in sorted(keylist, reverse=True):
                if key not in incomes.keys():
                    incomes[key] = temp_dict[key]
                    if key == this_year - num_years:
                        return incomes
        return incomes
    except TypeError:
        return None
    except IndexError:
        return None


#ticker = "pih"
#incomes = get_past_net_income(ticker, 5)
#if incomes is None:
#    print("Not able to extract! " + ticker)
#else:
#    for key, value in incomes.items():
#        print(str(key) + " " + str(value))
