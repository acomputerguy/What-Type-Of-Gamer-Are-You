import sys
import logging.config
from app.lambas.NewGamesChecker import NewGamesChecker
from app.profile.AnalyzeHabits import AnalyzeHabits

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

    # Analyze gaming habits
    # AnalyzeHabits.checkSteam()

