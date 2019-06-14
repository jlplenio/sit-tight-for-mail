import json
import os
import re
import time

from bot import Bot, dbcursor, db


class ImmoscoutBot(Bot):
    # Select&Insert-Statements
    s_latestimmos = """SELECT `immoid` FROM `immoscout` WHERE searchid = %s  ORDER BY id DESC"""
    i_immo = """ INSERT INTO `immoscout`( id, searchid ,immoid, titel, miete, qm, zimmer, adresse, date, link)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) """

    json_data = open(os.path.join(os.getcwd(), 'immoscout_config.json')).read()
    json_searches = {i: j for i, j in json.loads(json_data).items() if j != {}}

    def select_from_db(self, search):
        dbcursor.execute(self.s_latestimmos, search)
        data = dbcursor.fetchall()
        latest = []
        for row in data:
            latest.append(row[0])
        return latest

    def get_link(self, search):
        return self.json_searches[search]['link']

    def process_soup(self, soup):

        immos = soup.find_all('article', class_='result-list-entry')
        allimmos = []

        for immo in immos:

            immoid = immo.find('a', class_='result-list-entry__brand-title-container')['data-go-to-expose-id']
            titel = immo.find('h5',
                              class_=re.compile('result-list-entry__brand-title font-h6 onlyLarge nine-tenths*')).text

            miete_qm_zimmer = [i.text for i in immo.find_all('dd', class_='font-nowrap font-line-xs')]

            if len(miete_qm_zimmer) != 3:  # check if all three items found
                print("### ImmoscoutBot - 1 Immo SKIPPED !")
                continue

            else:
                miete = re.match("[\d,]+", miete_qm_zimmer[0].strip()).group(0)
                qm = re.match("[\d,]+", miete_qm_zimmer[1].strip()).group(0)
                zimmer = re.match("[\d,]+", miete_qm_zimmer[2].strip()).group(0)

            adresse = immo.find('button', class_='button-link link-internal result-list-entry__map-link').text

            link = "https://www.immobilienscout24.de/expose/" + immoid

            allimmos.append({
                'immoid': immoid,
                'titel': titel,
                'miete': miete.replace(".", "").replace(',', '.'),  # delete dots, then replace comma with dots
                'qm': qm.replace(".", "").replace(',', '.'),
                'zimmer': zimmer.replace(".", "").replace(',', '.'),
                'adresse': adresse,
                'link': link,
            })

        return list(reversed(allimmos))

    def filter_content(self, search, immos):
        latest20 = self.select_from_db(search)
        neuedealz = [immo for immo in immos if immo['immoid'] not in [str(oldimmoid) for oldimmoid in latest20]]
        return neuedealz

    def insert_in_db(self, search, immos):
        i = 0
        for immo in immos:
            dbcursor.execute(self.i_immo, (
                None, search, immo['immoid'], immo['titel'], immo['miete'], immo['qm'],
                immo['zimmer'], immo['adresse'], time.strftime('%Y-%m-%d %H:%M:%S'), immo['link']))
            i += 1
        db.commit()
        print(str(i) + " neue Immos eingetragen", time.strftime('%Y-%m-%d %H:%M:%S'))

    def worth_sending(self, search, immos):
        worth = [immo for immo in immos if "senior" not in immo['titel'].lower()]
        return worth

    def prepare_mail(self, immo):
        body = immo['titel'] + "\n" + immo['adresse'] + "\n" + immo['miete'] + " € - " + immo['qm'] + " qm - " + immo[
            'zimmer'] + " Zimmer" + "\n\n" + immo['link']
        subject = "[ImmoB07] " + immo['miete'] + "€ - " + immo['titel'][:60]
        return subject, body


""" MySQL table creation
CREATE TABLE IF NOT EXISTS `immoscout` (
`id` int(11) NOT NULL AUTO_INCREMENT,
  `searchid` varchar(10) NOT NULL,
  `immoid` int(11) NOT NULL,
  `titel` varchar(200) DEFAULT NULL,
  `miete` float DEFAULT NULL,
  `qm` float DEFAULT NULL,
  `zimmer` float DEFAULT NULL,
  `adresse` varchar(200) DEFAULT NULL,
  `date` datetime NOT NULL,
  `link` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;
"""
