import logging
from logging.config import fileConfig

class NewGamesChecker:

    logging.config.fileConfig('app/log/logging.conf')
    loggerConsole = logging.getLogger('ConsoleLogger')
    loggerFile = logging.getLogger('FileLogger')
    loggerConsole.addHandler(loggerFile)

    def is_new_game():
        NewGamesChecker.loggerConsole.info("Beginning check for a new game")
        # Helper method to demonstrate from /data/local file first, before querying the website.
        # url: https://api.steampowered.com/ISteamApps/GetAppList/v2/


# TODO with new game checker
# 1) use a hash to see if there is a new game
# 2) simulate with a small # of games to parse through
# 3) simulate with a large # of games to parse through, unicode exceptions
# 4) store small set of data into database as an example
# 5) store remaining data in db