from chat.ChatManager import ChatManager
from config import db_name, db_host, db_port, db_user, db_password

from conversation.ConversationRepository import ConversationRepository
from document.DocumentsRepository import DocumentsRepository
from embeddings.EmbeddingRepository import EmbeddingRepository
from message.MessageRepository import MessageRepository



class EmbeddingRepositoryProvider:
    def get_dependency(self) -> EmbeddingRepository:
        return EmbeddingRepository()


class DocumentDAOProvider:
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
        return DocumentsRepository(
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
        return ConversationRepository(
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
        return MessageRepository(
            db_name=self.db_name,
            db_host=self.db_host,
            db_port=self.db_port,
            db_user=self.db_user,
            db_password=self.db_password
        )


class ChatManagerProvider:
    def get_dependency(self) -> ChatManager:
        return ChatManager()


document_dao_provider = DocumentDAOProvider(
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