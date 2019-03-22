import json
import os
import time
import re

from collections import OrderedDict
from bot import Bot, db, dbcursor

class MydealzBot(Bot):
    """
    Crawls mydealz deals-new page, inserts deals into db and checks against searchwords.

    """

    # Select&Insert-Statements
    s_latestdealids = "SELECT `dealid` FROM mydealz ORDER by id desc limit 30"
    i_deal = """ INSERT INTO `mydealz`(`id`, `titel`, `stext`, `ltext`, `dlink`, `hlink`, `datum`, `price`, `dealid`)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) """

    json_data = open(os.path.join(os.getcwd(), 'mydealz_config.json')).read()
    json_searches = {i: j for i, j in json.loads(json_data).items() if j != {}}  # Dict comprehension BITCH
    json_searches = OrderedDict(sorted(json_searches.items()))

    def select_from_db(self, search):
        dbcursor.execute(self.s_latestdealids)
        data = dbcursor.fetchall()
        latest = []
        for row in data:
            latest.append(row[0])
        return latest

    def get_link(self, search):
        return "http://www.mydealz.de/deals-new"

    def process_soup(self, soup):

        deals = soup.find_all('article', class_='thread thread--type-list thread--deal')
        alldealz = []

        for deal in deals:
            titel = deal.find('a', class_='cept-tt thread-link linkPlain thread-title--list').text
            dealid = deal['id'][7:]
            dlink = deal.find('a', class_='cept-tt thread-link linkPlain thread-title--list')['href']
            stext = ""
            #stext = deal.find('div', class_='cept-description-container overflow--wrap-break size--all-s size--fromW3-m').text
            hlink = deal.find('a', class_=re.compile('cept-dealBtn boxAlign-jc--all-c space--h-3 width--all-12 btn btn--mode-primary.*'))['href'] if deal.find('a', target='_blank') else None
            price = deal.find('span', class_='thread-price text--b vAlign--all-tt cept-tp size--all-l size--fromW3-xl').text[:-1].replace(',', '.') if deal.find('span', class_='thread-price') else ""
            alldealz.append({
                'titel': titel.lstrip(),
                'dealid': dealid,
                'stext': stext,
                'dlink': dlink,
                'hlink': hlink,
                'price': price
            })
        return list(reversed(alldealz))

    def filter_content(self, search, deals):
        latest20 = self.select_from_db(search)
        neuedealz = [deal for deal in deals if deal['dealid'] not in [str(olddealid) for olddealid in latest20]]
        return neuedealz

    def insert_in_db(self, search, datadict):
        if search == list(self.json_searches.keys())[-1]:
            i = 0
            for deal in datadict:
                dbcursor.execute(self.i_deal, (
                    None, deal['titel'], deal['stext'], None, deal['dlink'], deal['hlink'],
                    time.strftime('%Y-%m-%d %H:%M:%S'), deal['price'], deal['dealid']))  # meh
                i += 1
            db.commit()
            print(str(i) + " neue Dealz eingetragen", time.strftime('%Y-%m-%d %H:%M:%S'))

    def worth_sending(self, search, neuedealz):

        deals2send = []
        for deal in neuedealz:
            dealtext = deal['stext'].lower() + " " + deal['titel'].lower()
            for keyword in self.json_searches[search]['keywords']:
                if isinstance(keyword, list):
                    if all(word.lower() in dealtext for word in keyword):
                        print("Multiple Hit on '" + ','.join(keyword) + "' -> " + deal['titel'])
                        deals2send.append([','.join(keyword), deal])
                        break
                elif keyword.lower() in dealtext:
                    print("Single Hit on '" + keyword + "' -> " + deal['titel'])
                    deals2send.append([keyword, deal])
                    break

        return deals2send

    def prepare_mail(self, item):
        keyword, deal = item
        body = str(deal['titel']) + "\n\n" + str(deal['stext']) + "\n" + str(deal['dlink']) + "\n" + str(deal['hlink']) + "\n\n" + "Einen wundervollen Tag, bye"
        subject = "[MyDealB07] found '" + keyword + "' für " + deal['price'] + " - " + deal['titel'][:40]
        return subject, body



"""MySQL table creation
CREATE TABLE IF NOT EXISTS `mydealz` (
`id` int(11) NOT NULL AUTO_INCREMENT,
  `titel` varchar(200) NOT NULL,
  `stext` varchar(250) NOT NULL,
  `ltext` longtext,
  `dlink` varchar(250) DEFAULT NULL,
  `hlink` varchar(250) DEFAULT NULL,
  `datum` datetime DEFAULT NULL,
  `dealid` int(11) DEFAULT NULL,
  `price` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;
"""