

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
# ROA = Net Income / Total Assets

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
    income_table, income_cell = find_net_income(tables)
    years = get_all_income_years(income_table)
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
        else:
            return None
    return years, net_incomes


#Need to look at how to get net loss
def find_net_income(tables):
    for table in tables:
        cells = table.find_all('td')
        for cell in cells:
            text = get_cell_text(cell)
            if text == "Net income" or text == "Net income (loss)" or text == "Net earnings":
                return table, cell


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
                text = text.replace(',', ', ')
                date = parse(text)
                year = date.year
                if is_valid_year(year):
                    found_year_row = True
                    years.append(year)
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
    text = cell.get_text()
    if (text is None or len(text) is 0) and len(cell.contents) > 0:
        text = cell.contents[0].get_text()
    text = text.replace('\n', '')
    #text = text.split('(')
    #text = text[0]
    text = text.strip()
    return text


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


def get_past_ten_years_net_income(ticker):
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
        temp_dict = dict()
        years, net_incomes = get_all_net_incomes(tables)
        for year, income in zip(years, net_incomes):
            temp_dict[year] = income
        keylist = temp_dict.keys()
        for key in sorted(keylist, reverse=True):
            if key not in incomes.keys():
                incomes[key] = temp_dict[key]
                if key == this_year - 10:
                    return incomes
    return incomes


incomes = get_past_ten_years_net_income("amd")
for key, value in incomes.items():
    print(str(key) + " " + str(value))