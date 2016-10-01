#!/usr/bin/env python

from bs4 import BeautifulSoup
from requests import get
from smtplib import SMTP
from email.mime.text import MIMEText
import pymysql, time, os


class Bot():
    def prepareMail(self, *args):

        raise NotImplementedError()

    def fetchContent(self):
        content = get(self.getLink())
        return BeautifulSoup(content.content, "html.parser")

    def selectLast20(self):
        raise NotImplementedError()

    def sendMail(self, to, subject, body):
        msg = MIMEText(body, 'plain')
        msg['To'] = to
        msg['Subject'] = subject
        msg['From'] = smtp_config['from']

        smtp = SMTP(host=smtp_config['host'], port=smtp_config['port'])
        smtp.ehlo()
        smtp.starttls()
        smtp.login(smtp_config['user'], smtp_config['pass'])
        smtp.sendmail(smtp_config['from'], to, msg.as_string().encode("utf8"))
        print("Mail versendet")

    def processSoup(self, soup):
        raise NotImplementedError()

    def filterContent(self, prossesed):
        raise NotImplementedError()

    def insertDeal(self, datadict):
        raise NotImplementedError()

    def dealEintragen(self, neuedealz):
        raise NotImplementedError()

    def h101Preis(self):
        raise NotImplementedError()


class MydealzBot(Bot):
    def selectLast20(self):
        dbcursor.execute(s_latestdealcode)
        data = dbcursor.fetchall()
        latest = []
        for row in data:
            latest.append(row[1])
        return latest

    def getLink(self):
        return "http://www.mydealz.de/deals-new"

    def processSoup(self, soup):
        dealtitel = soup.find_all('a', class_='section-title-link space--after-2')
        print(dealtitel)
        dealstext = soup.find_all('div', class_='section-sub text--word-wrap')
        haendlerlink = soup.find_all('a', href=True)
        haendlerlink = [link['href'] for link in haendlerlink if "visit" in link['href']]
        # Deals koennen keine haendlerlinks enthalten, damit verschiebt sich der dictaufbau und wird misaligned 20!=19
        alldealz = []
        for a, b, c in zip(dealtitel, dealstext, haendlerlink):
            print(a.contents[0])
            alldealz.append({
                'titel': a.contents[0],
                'stext': "".join([s for s in b.contents[0].strip().splitlines(True) if s.strip()]),
                'dlink': a.get('href'),
                'hlink': c
            })
        return reversed(alldealz)

    def filterContent(self, newest):
        latest20 = self.selectLast20()
        neuedealz = [deal for deal in newest if
                     deal['dlink'].split('-', )[-1] not in [oldeal.split('-', )[-1] for oldeal in latest20]]
        return neuedealz

    def worthSending(self, neuedealz, search):
        deals2send = []
        for deal in neuedealz:
            dealtext = deal['stext'].lower() + " " + deal['titel'].lower()
            for keyword in search['searchwords']:
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

    def prepareMail(self, keyword, deal):
        body = deal['titel'] + "\n\n" + deal['stext'] + "\n\n" + deal['dlink']
        subject = "[MyDealBot] found '" + keyword + "' - " + deal['titel'][:45]
        return subject, body

    def dealEintragen(self, neuedealz):
        i = 0
        for deal in neuedealz:
            dbcursor.execute(i_deal, (
            None, deal['titel'], deal['stext'], None, deal['dlink'], deal['hlink'], time.strftime('%Y-%m-%d %H:%M:%S')))
            # print(deal['titel'])
            i += 1
        db.commit()
        print(str(i) + " neue Dealz eingetragen")


class PriceChecker(Bot):
    def getLink(self):
        return "http://www.gearbest.com/rc-quadcopters/pp_230472.html"

    def processSoup(self, soup):
        price = soup.find_all('span', class_='my_shop_price new_shop_price')[0].contents[0]
        return price

    def filterContent(self, price):
        pass

credentials = []
with open('/home/scriptbot/mydealz_bot/secret.txt') as f:
    credentials = f.read().split(':')

searches = [
    {
        'to': "ubtown@gmail.com",
        'searchwords': ["Nespresso", "Drone", "Heide", "Heide Park", "oliver", "s.oliver", ["deine", "mudda"],
                        "v-server", "nexus", "8 TB", "8TB", "Markus", "Bioshock", "Human Revolution"]},

    {
        'to': "",
        'searchwords': ["lol"]},
]

smtp_config = {
    'host': "smtp.openmailbox.org",
    'port': 587,
    'user': credentials[0],
    'pass': credentials[1],
    'from': credentials[0],
}

# Open database connection
db = pymysql.connect(host='localhost', port=3306, user=credentials[2], passwd=credentials[2], db=credentials[2],
                     charset='utf8')
dbcursor = db.cursor()

# Select&Insert-Anweisungen
s_projekt = "SELECT `id`, `titel`, `stext`, `ltext`, `dlink`, `hlink`, `datum` FROM `mydealz`"
s_latestdealcode = "SELECT `id`,`dlink` FROM mydealz ORDER by id desc limit 30"

i_deal = """ INSERT INTO `mydealz`(`id`, `titel`, `stext`, `ltext`, `dlink`, `hlink`, `datum`) VALUES (%s, %s, %s, %s, %s, %s, %s) """


def main():
    bot = MydealzBot()
    soup = bot.fetchContent()
    processed = bot.processSoup(soup)
    filtered = bot.filterContent(processed)
    bot.dealEintragen(filtered)
    sendmenow = []
    for search in searches:
        tosendlist = bot.worthSending(filtered, search)
        for item in tosendlist:
            subject, body = bot.prepareMail(*item)
            sendmenow.append([search['to'], subject, body])

    for sendme in sendmenow:
        bot.sendMail(*sendme)


print("lol")
