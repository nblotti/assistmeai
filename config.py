import logging
import os

from dotenv import load_dotenv

# PostgreSQL connection details

os.environ["DB_NAME"] = ""
os.environ["DB_NAME_RAG"] = ''
os.environ["DB_HOST"] = ""
os.environ["DB_PORT"] = ""
os.environ["DB_USER"] = ""
os.environ["DB_PASSWORD"] = ""

os.environ["AZURE_OPENAI_API_KEY"] = ""
os.environ["AZURE_OPENAI_ENDPOINT"] = ""
os.environ["AZURE_GPT_35_API_VERSION"] = ""
os.environ["AZURE_GPT_35_CHAT_DEPLOYMENT_NAME"] = ""

os.environ["AZURE_GPT_4_API_VERSION"] = ""
os.environ["AZURE_GPT_4_CHAT_DEPLOYMENT_NAME"] = ""

os.environ["AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT_NAME"] = ""
os.environ["AZURE_OPENAI_EMBEDDINGS_API_VERSION"] = ""

os.environ["POSTGRES_INDEX_NAME"] = "AZQORE_CHAT"
os.environ[
    "PGVECTOR_CONNECTION_STRING"] = f"postgresql+psycopg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME_RAG')}?sslmode=require"

jwt_secret_key = ''
# Algorithm for token generation
jwt_algorithm = 'HS256'

ldap_url = ""
ldap_password = "",


def load_config():
    global db_password

    logging.basicConfig(level=logging.DEBUG)
    logging.info("-----------------------------------------------------------------------------------------------")
    logging.info("loading config")
    load_dotenv()

    if os.getenv("ENVIRONNEMENT") == "PROD":
        logging.info("Starting in PROD mode")
        db_password = os.getenv("DB_PASSWORD")
    else:
        logging.info("Starting in DEV mode")
