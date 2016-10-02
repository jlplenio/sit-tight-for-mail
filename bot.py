#!/usr/bin/env python

from email.mime.text import MIMEText
from smtplib import SMTP
from bs4 import BeautifulSoup
from requests import get

import json
import pymysql
import time

# better to use while open here?
json_data=open('config.json').read()
json_config = json.loads(json_data)

# ToDo: Close DB connection
# Open database connection
db = pymysql.connect(host=json_config['sql']['Host'], port=int(json_config['sql']['Port']),
                     user=json_config['sql']['User'], passwd=json_config['sql']['Pass'],
                     db=json_config['sql']['DB'], charset='utf8')
dbcursor = db.cursor()


class Bot:


    def prepare_mail(self, *args):
        raise NotImplementedError()

    def fetch_content(self):
        content = get(self.get_link())
        return BeautifulSoup(content.content, "html.parser")

    def select_from_db(self):
        raise NotImplementedError()

    def send_mail(self, to, subject, body):
        msg = MIMEText(body, 'plain')
        msg['To'] = to
        msg['Subject'] = subject
        msg['From'] = json_config['mail']['From']

        smtp = SMTP(host=json_config['mail']['Host'], port=json_config['mail']['Port'])
        smtp.ehlo()
        smtp.starttls()
        smtp.login(json_config['mail']['User'], json_config['mail']['Pass'])
        smtp.sendmail(json_config['mail']['From'], to, msg.as_string().encode("utf8"))
        print("Mail versendet")

    def process_soup(self, soup):
        raise NotImplementedError()

    def filter_content(self, processed):
        raise NotImplementedError()

    def insert_in_db(self, datadict):
        raise NotImplementedError()

    def get_link(self):
        raise NotImplementedError()

    def worth_sending(self, items, search):
        raise NotImplementedError()

class MydealzBot(Bot):

    # Select&Insert-Statements
    s_latestdeadids = "SELECT `dealid` FROM mydealz ORDER by id desc limit 30"
    i_deal = """ INSERT INTO `mydealz`(`id`, `titel`, `stext`, `ltext`, `dlink`, `hlink`, `datum`, `price`, `dealid`)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) """

    # better to use while open?
    json_data = open('mydealzsearches.json').read()
    json_searches = json.loads(json_data)

    def prepareMail(self, *args):
        pass

    def h101_preis(self):
        pass

    def select_from_db(self):
        dbcursor.execute(self.s_latestdeadids)
        data = dbcursor.fetchall()
        latest = []
        for row in data:
            latest.append(row[0])
        return latest

    def get_link(self):
        return "http://www.mydealz.de/deals-new"

    def process_soup(self, soup):

        deals = soup.find_all('article', class_='thread thread--deal thread--type-list space--mt-2')
        alldealz = []

        for deal in deals:

            # MakeMoreBeautiful IfElse
            titel = deal.find('a', class_='cept-tt linkPlain space--r-1 space--v-1').text
            dealid = deal['id'][7:]
            dlink = deal.find('a', class_='cept-tt linkPlain space--r-1 space--v-1')['href']
            stext = deal.find('div', class_='userHtml overflow--wrap-break space--t-2 space--b-1 hide--toW3').text
            hlink = deal.find('a', target='_blank')['href'] if deal.find('a', target='_blank') else None
            price = deal.find('span', class_='thread-price').text[:-1].replace(',','.') if deal.find('span',
                                                                                    class_='thread-price') else 0
            # stext = "".join([s for s in stext.strip().splitlines(True) if s.strip()]),


            alldealz.append({
                'titel': titel,
                'dealid': dealid,
                'stext': stext,
                'dlink': dlink,
                'hlink': hlink,
                'price': price
            })

        return reversed(alldealz)

    def filter_content(self, deals):
        latest20 = self.select_from_db()
        neuedealz = [deal for deal in deals if deal['dealid'] not in [str(olddealid) for olddealid in latest20]] #meh
        return neuedealz

    def worth_sending(self, neuedealz, search):
        """
        :param neuedealz: List of dealsdicts
        :param search: keywordslist from searches
        :return: [[keyword, deal],]
        """

        deals2send = []
        for deal in neuedealz:
            dealtext = deal['stext'].lower() + " " + deal['titel'].lower()
            for keyword in search['keywords']:
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

    def prepare_mail(self, keyword, deal):
        body = deal['titel'] + "\n\n" + deal['stext'] + "\n\n" + deal['dlink']
        subject = "[MyDealBot] found '" + keyword + "' für " + deal['price'] + " - " + deal['titel'][:40]
        return subject, body

    def insert_in_db(self, datadict):
        i = 0
        for deal in datadict:
            print("Found: " + deal['titel'] + " ------> " + str(deal['price']))
            dbcursor.execute(self.i_deal, (
                None, deal['titel'], deal['stext'], None, deal['dlink'], deal['hlink'],
                time.strftime('%Y-%m-%d %H:%M:%S'),float(deal['price']),deal['dealid'])) #meh
            i += 1
        db.commit()
        print(str(i) + " neue Dealz eingetragen")


class PriceChecker(Bot):
    def worth_sending(self, items, search):
        pass

    def insert_in_db(self, datadict):
        pass

    def prepare_mail(self, *args):
        pass

    def get_link(self):
        return "http://www.gearbest.com/rc-quadcopters/pp_230472.html"

    def process_soup(self, soup):
        price = soup.find_all('span', class_='my_shop_price new_shop_price')[0].contents[0]
        price = round(float(price) * 0.90998951, 2)
        return price

    def filter_content(self, price):
        pass

def main():
    bot = MydealzBot()
    soup = bot.fetch_content()
    processed = list(bot.process_soup(soup))
    filtered = bot.filter_content(processed)
    bot.insert_in_db(filtered)
    sendmenow = []
    for search in bot.json_searches:
        if bot.json_searches[search]:  # if content in subdict, e.g. search3['email']
            tosendlist = bot.worth_sending(filtered, bot.json_searches[search])
            for item in tosendlist:
                subject, body = bot.prepare_mail(*item)
                sendmenow.append([bot.json_searches[search]['email'], subject, body])
    for sendme in sendmenow:
        bot.send_mail(*sendme)


main()




