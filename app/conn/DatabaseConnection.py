import logging
from logging.config import fileConfig
import configparser
import mysql.connector

#SELECT * FROM game_info.game_data;

class DatabaseConnection:
    # fileConfig('logging_config.ini')
    # logger = logging.getLogger()
    logging.config.fileConfig('app/log/logging.conf')
    loggerConsole = logging.getLogger('ConsoleLogger')
    loggerFile = logging.getLogger('FileLogger')
    loggerConsole.addHandler(loggerFile)

    config = configparser.RawConfigParser()
    config.read('app/properties/local.properties')

    def connectToDatabase():
        DatabaseConnection.loggerConsole.info("Connecting to database")

        host = DatabaseConnection.config.get('MySQLDatabase', 'host')
        user = DatabaseConnection.config.get('MySQLDatabase', 'user')
        pwd = DatabaseConnection.config.get('MySQLDatabase', 'password')
        auth_plugin = DatabaseConnection.config.get('MySQLDatabase', 'auth_plugin')
        databaseSchema = DatabaseConnection.config.get('MySQLDatabase', 'databaseSchema')

        dbConn = mysql.connector.connect(
            host=host,
            user=user,
            password=pwd,
            auth_plugin=auth_plugin,
            database=databaseSchema
        )
        return dbConn