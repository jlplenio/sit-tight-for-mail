#from pricecheck_bot import PricecheckBot
from mydealz_bot import MydealzBot
from immoscout_bot import ImmoscoutBot

def main():
    for bot in [ImmoscoutBot(),MydealzBot()]:
        for search in bot.json_searches:
            maillist = []
            soup = bot.fetch_content(search)
            processed = (bot.process_soup(soup))
            filtered = bot.filter_content(search, processed)
            bot.insert_in_db(search, filtered)
            tosendlist = bot.worth_sending(search, filtered)
            for item in tosendlist:
                subject, body = bot.prepare_mail(item)
                maillist.append([bot.json_searches[search]['email'], subject, body])
            for mail in maillist:
                bot.send_mail(*mail)

main()