import logging
import os

from dotenv import load_dotenv

model_35 = "gpt-3.5-turbo-1106"
model_4 = "gpt-4-0125-preview"
model_lama = "gpt-4-0125-preview"
use_model = model_35

ai_request_timeout = 25

data_format_str = "%Y-%m-%d %H:%M:%S"


def load_config():
    global eod_quote_url
    logging.basicConfig(level=logging.DEBUG)
    logging.info("-----------------------------------------------------------------------------------------------")
    logging.info("loading config")
    load_dotenv()
    if os.getenv("ENVIRONNEMENT") == "PROD":
        logging.info("Starting in PROD mode")
        eod_quote_url = "http://market-data-cluster/quotes/{0}/{1}"
    else:
        logging.info("Starting in DEV mode")
        eod_quote_url = "https://marketdata.nblotti.org/quotes/{0}/{1}"

    logging.info("-----------------------------------------------------------------------------------------------")
