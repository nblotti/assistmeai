import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file, if present
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# PostgreSQL connection details set via environment variables
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
os.environ["AZURE_GPT_35_CHAT_MODEL_NAME"] = ""
os.environ["AZURE_GPT_4_API_VERSION"] = ""
os.environ["AZURE_GPT_4_CHAT_DEPLOYMENT_NAME"] = ""
os.environ["AZURE_GPT_4_CHAT_MODEL_NAME"] = ""

os.environ["AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT_NAME"] = ""
os.environ["AZURE_OPENAI_EMBEDDINGS_API_VERSION"] = ""
os.environ["AZURE_OPENAI_EMBEDDINGS_MODEL_VERSION"] = ""

os.environ["POSTGRES_INDEX_NAME"] = ""
os.environ["PGVECTOR_CONNECTION_STRING"] = (
    f"postgresql+psycopg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME_RAG')}?sslmode=require"
)

# JWT and LDAP configurations
jwt_secret_key = ''
jwt_algorithm = ''
ldap_url = ""
ldap_base_dn = ""
ldap_password = ""


def load_config():
    logging.info("--------------------------------------------------------")
    logging.info("Loading config")

    environment = os.getenv("ENVIRONNEMENT")
    logging.info(f"Environment: {environment}")

    if environment == "PROD":
        logging.info("Starting in PROD mode")
        set_verbose(False)
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
