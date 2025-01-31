import requests
import logging
import datetime
import os
import filecmp
import json
from datetime import datetime
import configparser

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

    config = configparser.ConfigParser()
    config.read('app/properties/local.properties')

    def is_new_game():
        NewGamesChecker.loggerConsole.info("Beginning check for a new game")
        #NewGamesChecker.download_all_games()
        conn = NewGamesChecker.connect_2_cluster()
        changedGames = NewGamesChecker.check_for_changes()
        NewGamesChecker.insert_games(conn[0], conn[1], changedGames[0], changedGames[1])

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
        return added_games, removed_games

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

    def connect_2_cluster(): # move to conn folder
        NewGamesChecker.loggerConsole.info("Establishing connection to Atlas Cluster on MongoDB")

        clientURL = ""
        databaseName = ""

        try:
            clientURL = os.environ['clientURL']
            databaseName = os.environ['databaseName']
        except KeyError as keyErr:
            NewGamesChecker.loggerConsole.info(f'Issue with reading configuration: {keyErr}')

        client = MongoClient(clientURL, tls=True, tlsAllowInvalidCertificates=True) # Use SSL

        collectionName = NewGamesChecker.config['MongoDB']['collectionName']
        db = client.get_database(databaseName).get_collection(collectionName)

        return db, databaseName

    def insert_games(db, dbName, addedGames, removedGames):

        NewGamesChecker.loggerConsole.info(f"Begin insert/update operations on documents from {dbName}")

        # Create primary all_games collection with values
        # Helper method with 1 time use
        NewGamesChecker.insert_base_helper(db)

        # Updating removed games
        # Changes the update time if run again - same appid can be removed more than once.
        NewGamesChecker.update_removed_games(db, removedGames)

        # Adding new games
        # Game can be renamed
        NewGamesChecker.update_added_games(db, addedGames)

    def insert_base_helper(db):
        NewGamesChecker.loggerConsole.info("Grabbing games from locally stored file")
        base_games = "data/all_games_1.tmp"
        # base_games = "data/all_games_2025-01-09.json.tmp"
        games_output = NewGamesChecker.make_set(base_games)

        insert_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

        allGamesList = []
        for game in games_output:
            allGamesList.append(
                {"_id": game.appid,
                 "name": game.name,
                 "removed": False,
                 "added": False,
                 "renamed": False,
                 "genre": "action, fighting",
                 "insert_date": insert_time,
                 "updated_date": "N/A",
                 "previous_name": ""}
            )

        allGamesLen = str(len(allGamesList))
        NewGamesChecker.loggerConsole.info(f"Inserting {allGamesLen} documents from all games into database")
        db.insert_many(allGamesList)

    def update_removed_games(db, removedGames):
        allRemovedGames = []
        for item in removedGames:
            allRemovedGames.append({'_id': item.appid})

        allRemovedLen = str(len(allRemovedGames))
        NewGamesChecker.loggerConsole.info(f"Updating {allRemovedLen} documents as removed games into database")
        update_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

        db.aggregate([
            {
                '$match': {
                    '$or': allRemovedGames
                }
            }, {
                '$set': {
                    'removed': True,
                    'updated_date': update_time
                }
            },
            {
                "$merge":
                 {
                     "into": "all_games",
                     "on": "_id",
                     "whenMatched": "replace"}
            }
        ])
        NewGamesChecker.loggerConsole.info(f"Completed updating {allRemovedLen} removed games")

    def update_added_games(db, addedGames):
        allAddedGames = []
        insert_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        for item in addedGames:
            allAddedGames.append(
                {"_id": item.appid,
                 "name": item.name,
                 "removed": False,
                 "added": True,
                 "renamed": False,
                 "genre": "action, fighting",
                 "insert_date": insert_time,
                 "updated_date": "N/A",
                 "previous_name": ""}
            )

        allAddedLen = str(len(allAddedGames))
        NewGamesChecker.loggerConsole.info(f"Inserting {allAddedLen} documents from added games into database")

        duplicateIds = []
        try:
            db.insert_many(allAddedGames, ordered=False) # unordered allows remaining games to be inserted
        except Exception as BulkWriteError:
            for err in BulkWriteError.details['writeErrors']:
                # duplicateIds.append({err['op']['_id'], err['op']['name']}) -> they come as a set
                gameid = {err['op']['_id']}
                name = {err['op']['name']}
                tempDict = {}
                for singleItem in gameid:
                    tempDict['appid'] = singleItem
                for singleItem in name:
                    tempDict['name'] = singleItem
                duplicateIds.append(tempDict)
            NewGamesChecker.loggerConsole.info(f"Duplicate appids {duplicateIds} already exist")
        # NewGamesChecker.loggerConsole.info(f"Updating names for appids {duplicateIds}")
        update_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        db.aggregate([
            {
                '$match': {
                    '_id': duplicateIds[0]['appid']
                }
            }, {
                '$set': {
                    'previous_name': {'$concat':['$name', ", ", '$previous_name']},
                    'name': duplicateIds[0]['name'],
                    'updated_date': update_time
                }
            },
            {
                "$merge":
                    {
                        "into": "all_games",
                        "on": "_id",
                        "whenMatched": "replace"}
            }
        ])

        # Games can be renamed
        # 3386350 Shinjuku Incident -> Shinjuku Anomaly
        # 1089671 "TFFP - DLC 02" -> "The Fisherman - Fishing Planet: Predator Boat Pack"
        # 3334690 japanese to english