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
    class GameData(object):
        def __init__(self, appid, name):
            self.appid = appid
            self.name = name
        def __hash__(self):
            return hash((self.appid, self.name))
        def __eq__(self, other):
            if not isinstance(other, type(self)): return NotImplemented
            return self.appid == self.appid
        def __str__(self):
            return f'appId: {self.appid}, name: {self.name}'

    logging.config.fileConfig('app/log/logging.conf')
    loggerConsole = logging.getLogger('ConsoleLogger')

    def is_new_game():
        NewGamesChecker.loggerConsole.info("Beginning check for a new game")
        #NewGamesChecker.download_all_games()
        NewGamesChecker.check_for_changes()

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
                f.write(all_games.text)
            f.close()

    def check_for_changes():

        yesterday = "data/all_games_2025-01-09.json.tmp"
        today = "data/all_games_2025-01-10.json.tmp"
        # yesterday = "data/all_games_1.tmp"
        # today = "data/all_games_2.tmp"

        NewGamesChecker.loggerConsole.info("Comparing two files to find difference")
        # Shallow set to true use os.stat() signatures (file type, size, modification) and not byte-by-byte
        result = filecmp.cmp(yesterday, today, shallow=False)

        if result:
            NewGamesChecker.loggerConsole.info("The files are identical")
        else:
            NewGamesChecker.loggerConsole.info("The files are different. Finding differences...")

            # Find non-duplicate game count number for yesterday and today
            yesterday_total = NewGamesChecker.day_set(yesterday)
            today_total = NewGamesChecker.day_set(today)
            NewGamesChecker.loggerConsole.info("Game count for yesterday: "
                                               + str(yesterday_total)
                                               + " and todays: "
                                               + str(today_total))

            # List removed and added games
            # NoSQL result:
            # Removed games - 39.9k
            # Added games - 88.7k
            # Python Set result:
            # Removed games - 65,375
            # Added games - 30,465
            # Confirmed duplicate examples 371660 2101210
            # Difference (set) adds up with 151,178 yesterdays and 186,088 today
            # But there is a discrepancy where 186088-151178 = 34910 and 30465 is actual count.
            # What happened to 4445 games?
            f = open("data/added_removed_games_set.log", "a")

            added_games = NewGamesChecker.find_diff_games(yesterday, today)
            removed_games = NewGamesChecker.find_diff_games(today, yesterday)

            f.write("Removed count: " + str(len(removed_games)) + "\n")
            for game in added_games: f.write(str(game) + "\n")
            f.write("Added count: " + str(len(added_games)) + "\n")
            for game in removed_games: f.write(str(game) + "\n")

            f.close()

    def find_diff_games(dateX, dateY):

        NewGamesChecker.loggerConsole.info("Searching for added or removed games")

        first_games_set = set()
        second_games_set = set()

        with open(dateX, 'r') as json_file:
            yesterday_dict = json.load(json_file)
            for game in yesterday_dict['applist']['apps']:
                first_games_set.add(NewGamesChecker.GameData(game['appid'], game['name']))
        json_file.close()

        with open(dateY, 'r') as json_file:
            today_dict = json.load(json_file)
            for game in today_dict['applist']['apps']:
                second_games_set.add(NewGamesChecker.GameData(game['appid'], game['name']))
        json_file.close()

        different_games = first_games_set.difference(second_games_set)

        return different_games

    def day_set(file):

        date_set = set()
        with open(file, 'r') as json_file:
            file_dict = json.load(json_file)
            for game in file_dict['applist']['apps']:
                date_set.add(NewGamesChecker.GameData(game['appid'], game['name']))
        json_file.close()

        return len(date_set)

        """
        yesterdays_games = yesterday_dict['applist']['apps']
        todays_games = today_dict['applist']['apps']

        counter = 0

        diff_games = []

        # Checks for a different game, be it removed or added
        for y_keyval in yesterdays_games:
            print("Checking for " + str(y_keyval['appid']))
            counter += 1
            percentage = counter / 230000 * 100
            print(percentage)
            for t_keyval in todays_games:
                game_found = False
                if y_keyval['appid'] == t_keyval['appid']:
                    game_found = True
                    # print("Appids match, breaking: " + str(y_keyval['appid']) + ", " + str(y_keyval['appid']))
                    break
                else:
                    pass
                    # print("No match, continuing search: " + str(y_keyval['appid']) + ", " + str(t_keyval['appid']) )
            if not game_found:
                # print("Appid does not exist, storing unique value: " + str(y_keyval))
                diff_games.append(y_keyval)

        return diff_games
        """

# TODO with new game checker
# 1) use a hash to see if there is a new game (done)
# 2) simulate with a small # of games to parse through (done)
# 3) simulate with a large # of games to parse through, unicode exceptions (pending)
# 4) store small set of data into database as an example
# 5) store remaining data in db