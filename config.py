import logging
import os

from dotenv import load_dotenv

from DependencyManager import EmbeddingRepositoryProvider, PostgresDAOProvider, \
    ConversationDAOProvider, PdfManagerProvider, MessageDAOProvider

url_entries: str = "https://portfolio.nblotti.org/simulation/command"
url_positions: str = "https://portfolio.nblotti.org/simulation/porfolio"


def load_config() -> PdfManagerProvider:
    logging.basicConfig(level=logging.DEBUG)
    logging.info("-----------------------------------------------------------------------------------------------")
    logging.info("loading config")
    load_dotenv()
    pdf_manager_provider: PdfManagerProvider
    global url_entries
    global url_positions

    if os.getenv("ENVIRONNEMENT") == "PROD":
        logging.info("Starting in PROD mode")

        url_entries = "http://portfolio-cluster/simulation/command"
        url_positions = "http://portfolio-cluster/simulation/porfolio"
        db_name = "rag"
        db_host = "rag.coenmrmhbaiw.us-east-2.rds.amazonaws.com"
        db_port = "5432"
        db_user = os.getenv("DB_PASSWORD")
        db_password = os.getenv("DB_PASSWORD")
        embedding_repository_provider = EmbeddingRepositoryProvider()

        postgres_dao_provider = PostgresDAOProvider(
            db_name=db_name,
            db_host=db_host,
            db_port=db_port,
            db_user=db_user,
            db_password=db_password
        )
        conversation_dao_provider = ConversationDAOProvider(
            db_name=db_name,
            db_host=db_host,
            db_port=db_port,
            db_user=db_user,
            db_password=db_password
        )
        message_dao_provider = MessageDAOProvider(
            db_name=db_name,
            db_host=db_host,
            db_port=db_port,
            db_user=db_user,
            db_password=db_password
        )
        return PdfManagerProvider(embedding_repository_provider, postgres_dao_provider,
                                  conversation_dao_provider, message_dao_provider)


    else:
        logging.info("Starting in DEV mode")
        url_entries= "https://portfolio.nblotti.org/simulation/command"
        url_positions = "https://portfolio.nblotti.org/simulation/porfolio"
        db_name = "rag"
        db_host = "rag.coenmrmhbaiw.us-east-2.rds.amazonaws.com"
        db_port = "5432"
        db_user = "postgres"
        db_password = "postgres"
        embedding_repository_provider = EmbeddingRepositoryProvider()
        postgres_dao_provider = PostgresDAOProvider(
            db_name=db_name,
            db_host=db_host,
            db_port=db_port,
            db_user=db_user,
            db_password=db_password
        )
        conversation_dao_provider = ConversationDAOProvider(
            db_name=db_name,
            db_host=db_host,
            db_port=db_port,
            db_user=db_user,
            db_password=db_password
        )
        message_dao_provider = MessageDAOProvider(
            db_name=db_name,
            db_host=db_host,
            db_port=db_port,
            db_user=db_user,
            db_password=db_password
        )
        return PdfManagerProvider(embedding_repository_provider, postgres_dao_provider,
                                  conversation_dao_provider, message_dao_provider)
