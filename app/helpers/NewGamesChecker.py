import requests
import logging

from logging.config import fileConfig
from app.helpers.enum.SteamEnums import SteamEnums

###
# To be: Lambda on AWS but running locally once
###

class NewGamesChecker:

    logging.config.fileConfig('app/log/logging.conf')
    loggerConsole = logging.getLogger('ConsoleLogger')

    def is_new_game():
        NewGamesChecker.loggerConsole.info("Beginning check for a new game")
        # Helper method to demonstrate from /data/local file first, before querying the website.
        all_games_url = SteamEnums.ALLGAMES.value
        all_games = requests.get(all_games_url)
        # String limit depends on platform and RAM amount. IDE complained and can incur short term mem costs




# TODO with new game checker
# 1) use a hash to see if there is a new game
# 2) simulate with a small # of games to parse through
# 3) simulate with a large # of games to parse through, unicode exceptions
# 4) store small set of data into database as an example
# 5) store remaining data in db