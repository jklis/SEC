

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

def get_document(link):
    res = requests.get(link)
    soup = BeautifulSoup(res.content, 'lxml')
    table = soup.select('table[summary="Document Format Files"]')
    doc_link = table[0].find('a').get('href')
    res = requests.get(base_link + doc_link)
    return res.content


def find_net_income(year, tables):
    for table in tables:
        cells = table.find_all('td')
        for cell in cells:
            text = get_cell_text(cell)
            if text == "Net income" or text == "Net income (loss)":
                column_num = find_column_num(year, table)
                net_income = get_n_num(column_num, cell)
                return net_income


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
    text = text.split('(')
    text = text[0]
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



def find_doc_year(doc):
    header_divs = doc.find_all("div", class_="infoHead")
    for div in header_divs:
        if div.get_text() == "Period of Report":
            date_text = div.next_sibling.get_text()



links, years = get_links("amd", "10-k")
if years[0] == this_year:
    index = 0
    for year in years:
        year -= 1
        years[index] = year
        index += 1
index = 0
for link in links:
    filing_doc = get_document(link)
    doc_soup = BeautifulSoup(filing_doc, 'lxml')
    tables = doc_soup.find_all('table')
    print(find_net_income(years[index], tables))
    index += 1
