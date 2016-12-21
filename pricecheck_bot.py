from bot import Bot, dbcursor  # funky import working?
import os, json, re

""" MySQL table creation
CREATE TABLE `pricechecker` ( `id` INT NOT NULL AUTO_INCREMENT, `name` VARCHAR(100) NOT NULL , `price`
FLOAT NOT NULL , `date` DATE NOT NULL , PRIMARY KEY (`id`)) ENGINE = InnoDB;
"""

class PricecheckBot(Bot):
    def __init__(self):

        with open(os.path.join(os.getcwd(), 'pricecheck_config.json')) as file:
            json_data = file.read()
            self.json_searches = json.loads(json_data)

    # Select&Insert-Statements
    s_latestprice = """SELECT `price` FROM `pricechecker` WHERE `name` = %s ORDER by `id` desc limit 1"""
    i_price = """ INSERT INTO `pricechecker`(`id`, `name`, `price`, `date`) VALUES (%s,%s,%s,%s) """

    def select_from_db(self):
        dbprices = []
        for search in self.json_searches:
            name = search['name']
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

    def get_link(self):
        linklist = []
        for search in self.json_searches:
            linklist.append()
        return linklist

    def process_soup(self, souplist):
        priceslist = []
        for search, soup in zip(self.json_searches, souplist):
            price = soup.find(search['tag'], search["att"])
            price = price.contents[0] if price else "0"
            match = re.match("^[\d\.]+$", price)
            priceslist.append(float(price) if match else 0)
        return priceslist

    def filter_content(self, prices):
        returndict = {}
        for search, price, old_price in zip(self.json_searches, prices, self.select_from_db()):
            if price != old_price:
                returndict[search['name']] = price
        return returndict


        # Fülle .insert_in_db
