import sys
import logging
import logging.config
from app.conn.DatabaseConnection import DatabaseConnection
from app.helpers.NewGamesChecker import NewGamesChecker

def show_banner():
    banner = open("app/misc/banner.txt")
    for line in banner:
        line = line.strip('\n')
        print(line, file=sys.stdout, flush=True)

if __name__ == '__main__':
    show_banner()

    logging.config.fileConfig('app/log/logging.conf')
    loggerConsole = logging.getLogger('ConsoleLogger')
    loggerConsole.info("Logging service initiated")

    # Checking for new games to run in background, separate from main application
    newgames = NewGamesChecker.is_new_game()


    # TODO with database
    # set up connection to database with models, queries to insert/remove (3 classes)
    # connect to steam api to get metadata from games
    # start with first 10 games from 100k games and download to database
    # daily job to check for new games with hash
    # loggerConsole.info("Initiating database connection")
    # dbConn = DatabaseConnection.connectToDatabase()


