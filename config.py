import logging
import os
import time
from functools import wraps

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class ExcludePathFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        excluded_path = "GET /job/"
        # If this substring is found, return False (exclude from logs)
        if excluded_path in record.getMessage():
            return False
        return True

access_logger = logging.getLogger("uvicorn.access")
# Add our custom filter to exclude /job/ paths
access_logger.addFilter(ExcludePathFilter())


Base = declarative_base()
SessionLocal = None
engine = None

os.environ["PGVECTOR_CONNECTION_STRING"] = (
    f"postgresql+psycopg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME_RAG')}?sslmode=require"
)


def init_db():
    global engine, SessionLocal

    engine = create_engine(os.getenv("PGVECTOR_CONNECTION_STRING"))
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency to get DB session
async def get_db():
    if SessionLocal is None:
        raise RuntimeError("SessionLocal is not initialized. Call init_db() first.")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
