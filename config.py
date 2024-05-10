import json
import logging
import os

from dotenv import load_dotenv


url_entries: str = "https://portfolio.nblotti.org/simulation/command"
url_positions: str = "https://portfolio.nblotti.org/simulation/porfolio"
db_name = "rag"
db_host = "rag.coenmrmhbaiw.us-east-2.rds.amazonaws.com"
db_port = "5432"
db_user = "postgres"
db_password = "postgres"


def load_config():
    global url_entries
    global url_positions
    global db_password

    logging.basicConfig(level=logging.DEBUG)
    logging.info("-----------------------------------------------------------------------------------------------")
    logging.info("loading config")
    load_dotenv()

    if os.getenv("ENVIRONNEMENT") == "PROD":
        logging.info("Starting in PROD mode")

        url_entries = "http://portfolio-cluster/simulation/command"
        url_positions = "http://portfolio-cluster/simulation/porfolio"
        db_password = os.getenv("DB_PASSWORD")


    else:
        logging.info("Starting in DEV mode")
