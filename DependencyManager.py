from chat.ConversationDAO import ConversationDAO
from chat.MessageDAO import MessageDAO
from embeddings.EmbeddingRepository import EmbeddingRepository
from chat.InteractionManager import InteractionManager
from chat.DocumentsDAO import DocumentsDAO
from chat.SqliteDAO import SqliteDAO


class EmbeddingRepositoryProvider:
    def get_dependency(self) -> EmbeddingRepository:
        return EmbeddingRepository()


class PostgresDAOProvider:
    db_name: str
    db_host: str
    db_port: str
    db_user: str
    db_password: str

    def __init__(self, db_name: str, db_host: str, db_port: str, db_user: str, db_password: str):
        self.db_name = db_name
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_password = db_password

    def get_dependency(self):
        return DocumentsDAO(
            db_name=self.db_name,
            db_host=self.db_host,
            db_port=self.db_port,
            db_user=self.db_user,
            db_password=self.db_password
        )


class ConversationDAOProvider:
    db_name: str
    db_host: str
    db_port: str
    db_user: str
    db_password: str

    def __init__(self, db_name: str, db_host: str, db_port: str, db_user: str, db_password: str):
        self.db_name = db_name
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_password = db_password

    def get_dependency(self):
        return ConversationDAO(
            db_name=self.db_name,
            db_host=self.db_host,
            db_port=self.db_port,
            db_user=self.db_user,
            db_password=self.db_password
        )


class MessageDAOProvider:
    db_name: str
    db_host: str
    db_port: str
    db_user: str
    db_password: str

    def __init__(self, db_name: str, db_host: str, db_port: str, db_user: str, db_password: str):
        self.db_name = db_name
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_password = db_password

    def get_dependency(self):
        return MessageDAO(
            db_name=self.db_name,
            db_host=self.db_host,
            db_port=self.db_port,
            db_user=self.db_user,
            db_password=self.db_password
        )


# Define an outer dependency provider class
class PdfManagerProvider:
    def __init__(self, embedding_repository_provider: EmbeddingRepositoryProvider,
                 postgres_dao_provider: PostgresDAOProvider,
                 conversation_dao_provider: ConversationDAOProvider,
                 message_dao_provider: MessageDAOProvider):
        self.embedding_repositoryProvider = embedding_repository_provider
        self.postgres_dao_provider = postgres_dao_provider
        self.conversation_dao_provider = conversation_dao_provider
        self.message_dao_provider = message_dao_provider

    def get_dependency(self) -> InteractionManager:
        embedding_repository = self.embedding_repositoryProvider.get_dependency()
        postrgres_dao = self.postgres_dao_provider.get_dependency()
        conversation_dao = self.conversation_dao_provider.get_dependency()
        message_dao = self.message_dao_provider.get_dependency()
        return InteractionManager(embedding_repository, postrgres_dao, conversation_dao, message_dao)
