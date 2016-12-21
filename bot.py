#!/usr/bin/env python

from email.mime.text import MIMEText
from smtplib import SMTP
from bs4 import BeautifulSoup
from requests import get

import os
import json
import pymysql

json_data = open(os.path.join(os.getcwd(), 'bot_config.json')).read()
json_config = json.loads(json_data)

db = pymysql.connect(host=json_config['sql']['Host'], port=int(json_config['sql']['Port']),
                     user=json_config['sql']['User'], passwd=json_config['sql']['Pass'],
                     db=json_config['sql']['DB'], charset='utf8')
dbcursor = db.cursor()

class Bot:
    def get_link(self, search):
        raise NotImplementedError()

    def fetch_content(self, search):
        link = self.get_link(search)
        content = get(link)
        return BeautifulSoup(content.content, "html.parser")

    def process_soup(self, soup):
        raise NotImplementedError()

    def filter_content(self, search, processed):
        raise NotImplementedError()

    def select_from_db(self, search):
        raise NotImplementedError()

    def insert_in_db(self, search, datadict):
        raise NotImplementedError()

    def worth_sending(self, search, items):
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
        print("Mail verschickt an:",to)

