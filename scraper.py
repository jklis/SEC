

# F-Score Calculation:
# 1. Net Income
# 2. Return on Assets
# 3. Operating cash flow
# 4. Cash flow from operations being greater than net income (quality of earnings)
# 5. Lower ratio of long term debt in current period compared to previous year (decreased leverage)
# 6. Higher current ratio this year compared to previous year (more liquidity)
# 7. No new shares were issued in the previous year (lack of dilution)
# 8. A higher gross margin compared to the previous year
# 9. A higher asset turnover ratio compared to previous year

#


import re
import requests
from bs4 import BeautifulSoup
import datetime


base_link = "https://www.sec.gov"


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
    for date in dates:
        if date > datetime.datetime(2008, 1, 1).date():
            good_links.append(links[index])
            index += 1

    return good_links


def get_document(link):
    res = requests.get(link)
    soup = BeautifulSoup(res.content, 'lxml')
    table = soup.select('table[summary="Document Format Files"]')
    doc_link = table[0].find('a').get('href')
    res = requests.get(base_link + doc_link)
    return res.content


def find_net_income(tables):
    for table in tables:
        paragraphs = table.find_all('p')
        for p in paragraphs:
            text = p.get_text()
            if text == "Net income":
                print(text)
                #going to have to write something to find parent and sibling combination that produces the value based on where the next valid number is.
                net_income = p.parent.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.get_text()
                net_income = net_income.strip()
                net_income = net_income.replace(',', '')
                net_income = int(net_income)
                return net_income


links = get_links("goog", "10-k")
for link in links:
    filing_doc = get_document(link)
    doc_soup = BeautifulSoup(filing_doc, 'lxml')
    tables = doc_soup.find_all('table')
    print(find_net_income(tables))
