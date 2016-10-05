#!/usr/bin/env python

from email.mime.text import MIMEText
from smtplib import SMTP
from bs4 import BeautifulSoup
from requests import get

import os
import json
import pymysql
import time

# better to use while open here?
json_data=open(os.path.join(os.getcwd(), 'config.json')).read()
json_config = json.loads(json_data)

# ToDo: Close DB connection

# Open database connection
db = pymysql.connect(host=json_config['sql']['Host'], port=int(json_config['sql']['Port']),
                     user=json_config['sql']['User'], passwd=json_config['sql']['Pass'],
                     db=json_config['sql']['DB'], charset='utf8')
dbcursor = db.cursor()


class Bot:

    def get_links(self):
        raise NotImplementedError()

    def fetch_content(self):
        """
        Expects List from self.get_links
        :return: List of Soup objects
        """

        links = self.get_links()
        linklist = []
        for link in links:
            content = get(link)
            print(content)
            linklist.append(BeautifulSoup(content.content, "html.parser"))
        return linklist


    def process_soup(self, soup):
        raise NotImplementedError()

    def filter_content(self, processed):
        raise NotImplementedError()

    def select_from_db(self):
        raise NotImplementedError()

    def insert_in_db(self, datadict):
        raise NotImplementedError()

    def worth_sending(self, items, search):
        raise NotImplementedError()

    def prepare_mail(self, *args):
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


class MydealzBot(Bot):

    # Select&Insert-Statements
    s_latestdealids = "SELECT `dealid` FROM mydealz ORDER by id desc limit 30"
    i_deal = """ INSERT INTO `mydealz`(`id`, `titel`, `stext`, `ltext`, `dlink`, `hlink`, `datum`, `price`, `dealid`)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) """

    # better to use while open?
    json_data = open(os.path.join(os.getcwd(), 'mydealzsearches.json')).read()
    json_searches = {i: j for i, j in json.loads(json_data).items() if j != {}} #Dict comprehension BITCH
    #json_searches = collections.OrderedDict(json_searches)

    def select_from_db(self):
        dbcursor.execute(self.s_latestdealids)
        data = dbcursor.fetchall()
        latest = []
        for row in data:
            latest.append(row[0])
        return latest

    def get_links(self):
        return ["http://www.mydealz.de/deals-new"]

    def process_soup(self, soup):

        #soup[0] dirty dirty
        deals = soup[0].find_all('article', class_='thread thread--deal thread--type-list space--mt-2')
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

        return list(reversed(alldealz))

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
        #db.commit()
        print(str(i) + " neue Dealz eingetragen")


class PriceChecker(Bot):

    """
    CREATE TABLE `pricechecker` ( `id` INT NOT NULL AUTO_INCREMENT, `name` VARCHAR(100) NOT NULL , `price`  FLOAT NOT NULL , `date` DATE NOT NULL , PRIMARY KEY (`id`)) ENGINE = InnoDB;

    Weil Bot durch MydealzBot darauf getrimmt ist immer nur eine URL zu durchsuchen und
    dann nachträglich auf Keywords zu prüfen ist es super schwierig mehrere pricesearches
    auf unterschiedlichen seiten zu machen ... sehr hässlich bislang, da ich auf die
    reihenfolge der listen und dicts baue

    Und grrrrr an das Interface halten, wie ne Zwangsjacke
    """

    # Select&Insert-Statements
    s_latestprice = """SELECT `price` FROM `pricechecker` WHERE `name` = %s ORDER by `id` desc limit 1"""
    i_price = """ INSERT INTO `pricechecker`(`id`, `name`, `price`, `date`) VALUES (%s,%s,%s,%s) """

    # better to use while open?
    json_data = open(os.path.join(os.getcwd(), 'pricesearches.json')).read()
    json_searches = {i: j for i, j in json.loads(json_data).items() if j != {}} #Dict comprehension BITCH

    def select_from_db(self):
        dbprices = []
        for search in self.json_searches:
                name = self.json_searches[search]['name']
                dbcursor.execute(self.s_latestprice, name)
                price = dbcursor.fetchone()
                price = price[0] if price else None
                dbprices.append(price)
        return dbprices

    def worth_sending(self, items, search):
        pass

    def insert_in_db(self, datadict):
        pass

    def prepare_mail(self, *args):
        pass

    def get_links(self):
        linklist = []
        for search in self.json_searches:
                linklist.append(self.json_searches[search]['url'])
        return linklist

    def process_soup(self, souplist):
        priceslist = []
        i = 0
        #kA, wie ich über souplist iteriere, er cucked mich
        for search in self.json_searches:
            price = souplist[i].find(self.json_searches[search]['tag'], class_=self.json_searches[search]['class']).contents[0]
            priceslist.append(float(price))
            i += 1
        return priceslist

    def filter_content(self, price):
        print(self.select_from_db())
        print(price)
        # Continue


def main():
    bot = MydealzBot()
    soup = bot.fetch_content()
    processed = (bot.process_soup(soup))
    filtered = bot.filter_content(processed)
    bot.insert_in_db(filtered)
    sendmenow = []
    for search in bot.json_searches:
        tosendlist = bot.worth_sending(filtered, bot.json_searches[search])
        for item in tosendlist:
            subject, body = bot.prepare_mail(*item)
            sendmenow.append([bot.json_searches[search]['email'], subject, body])
    for sendme in sendmenow:
        bot.send_mail(*sendme)


bot = PriceChecker()
soup = bot.fetch_content()
processed = bot.process_soup(soup)
bot.filter_content(processed)







