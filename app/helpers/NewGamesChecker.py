import requests
import logging
import datetime
import os
import filecmp
import json

from logging.config import fileConfig
from pymongo import MongoClient
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
        NewGamesChecker.connect_2_cluster()
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

        # yesterday = "data/all_games_2025-01-09.json.tmp"
        # today = "data/all_games_2025-01-10.json.tmp"
        yesterday = "data/all_games_1.tmp"
        today = "data/all_games_2.tmp"

        NewGamesChecker.loggerConsole.info("Comparing two files to find difference")
        # Shallow set to true use os.stat() signatures (file type, size, modification) and not byte-by-byte
        result = filecmp.cmp(yesterday, today, shallow=False)

        if result:
            NewGamesChecker.loggerConsole.info("The files are identical")
        else:
            NewGamesChecker.loggerConsole.info("The files are different. Finding differences...")

            f = open("data/added_removed_games_set.log", "a")

            added_games = NewGamesChecker.find_diff_games(today, yesterday, False)
            removed_games = NewGamesChecker.find_diff_games(yesterday, today, True)

            f.write("Removed count: " + str(len(removed_games)) + "\n")
            for game in removed_games: f.write(str(game) + "\n")
            f.write("Added count: " + str(len(added_games)) + "\n")
            for game in added_games: f.write(str(game) + "\n")

            f.close()

    def find_diff_games(dateX, dateY, isAdd):

        if not isAdd:
            NewGamesChecker.loggerConsole.info("Searching for added games")
        else:
            NewGamesChecker.loggerConsole.info("Searching for removed games")

        first_games_set = NewGamesChecker.make_set(dateX)
        second_games_set = NewGamesChecker.make_set(dateY)

        # Find non-duplicate game count number for yesterday and today
        if isAdd:
            NewGamesChecker.loggerConsole.info("Game count for yesterday: "
                                               + str(len(first_games_set))
                                               + " and todays: "
                                               + str(len(second_games_set)))

        different_games = first_games_set.difference(second_games_set)

        return different_games

    def make_set(file):

        set_name = set()

        with open(file, 'r') as json_file:
            file_dict = json.load(json_file)
            for game in file_dict['applist']['apps']:
                set_name.add(NewGamesChecker.GameData(game['appid'], game['name']))
        json_file.close()

        return set_name

    def connect_2_cluster():
        NewGamesChecker.loggerConsole.info("Establishing connection to Atlas Cluster on MongoDB")

        clientURL = ""
        collectionName = ""

        try:
            clientURL = os.environ['clientURL']
            collectionName = os.environ['collectionName']
            # clientURL = NewGamesChecker.config['MongoDB']['clientURL']
            # collectionName = NewGamesChecker.config['MongoDB']['collectionName']
        except KeyError as keyErr:
            NewGamesChecker.loggerConsole.info(f'Issue with reading configuration: {keyErr}')

        client = MongoClient(clientURL, tls=True, tlsAllowInvalidCertificates=True) # Use SSL
        db = client[collectionName]
        documents = db.list_collection_names()

        print(documents)
