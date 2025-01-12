import requests
import logging
import datetime
import os
import filecmp
import json


from logging.config import fileConfig
from app.helpers.enum.SteamEnums import SteamEnums

###
# To be: Lambda on AWS but running locally once per day
###

class NewGamesChecker:

    logging.config.fileConfig('app/log/logging.conf')
    loggerConsole = logging.getLogger('ConsoleLogger')

    def is_new_game():
        NewGamesChecker.loggerConsole.info("Beginning check for a new game")
        #NewGamesChecker.download_all_games()
        NewGamesChecker.check_for_new_game()

    def download_all_games():
        # Helper method to demonstrate from /data/local file first, before querying the website.
        all_games_url = SteamEnums.ALLGAMES.value
        all_games = requests.get(all_games_url)

        today = datetime.date.today()
        NewGamesChecker.loggerConsole.info("Downloading all game list for today")

        if os.path.exists("data/all_games_" + str(today) + ".json.tmp"):
            NewGamesChecker.loggerConsole.info("Today's all_game file exists for " + str(today))
        else:
            # String limit depends on platform and RAM amount. IDE complained and can incur short term mem costs
            # At 12.5 MB for 220k+ games, Lambda has ephemeral storage of 512 MB. No need to redesign
            NewGamesChecker.loggerConsole.info("Today's all_game file does not exist. Creating data/all_games_" + str(today) + ".json.tmp")
            with open("data/all_games_" + str(today) + ".json.tmp", "x") as f:
                f.write(all_games.text) #all_games.text
            f.close()

    def check_for_new_game():

        NewGamesChecker.loggerConsole.info("Checking for change")
        # Shallow set to true use os.stat() signatures (file type, size, modification) and not byte-by-byte
        result = filecmp.cmp("data/all_games_2025-01-09.json.tmp", "data/all_games_2025-01-10_old.json.tmp", shallow=False)

        if result:
            print("The files are identical.")
        else:
            print("The files are different.")



# TODO with new game checker
# 1) use a hash to see if there is a new game (done)
# 2) simulate with a small # of games to parse through (done)
# 3) simulate with a large # of games to parse through, unicode exceptions (pending)
# 4) store small set of data into database as an example
# 5) store remaining data in db