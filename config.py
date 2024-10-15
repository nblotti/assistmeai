import logging
import os
import time
from functools import wraps

from dotenv import load_dotenv
if os.getenv("ENVIRONNEMENT") == "PROD":
    load_dotenv("config/.env")
else:
    load_dotenv()
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

os.environ["PGVECTOR_CONNECTION_STRING"] = (
    f"postgresql+psycopg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME_RAG')}?sslmode=require"
)

def load_config():
    global ldap_url
    logging.info("--------------------------------------------------------")
    logging.info("Loading config")




    environment = os.getenv("ENVIRONNEMENT")
    logging.info(f"Environment: {environment}")

    if environment == "PROD":
        logging.info("Starting in PROD mode")
    else:
        logging.info("Starting in DEV mode")

    logging.info("Config load complete")
    logging.info("--------------------------------------------------------")


def set_verbose(verbose: bool):
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Logging level set to DEBUG")
    else:
        logging.getLogger().setLevel(logging.INFO)
        logging.info("Logging level set to INFO")


def measure_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Time spent in {func.__name__}: {end_time - start_time} seconds")
        return result

    return wrapper
