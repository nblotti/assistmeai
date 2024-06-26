from chat.ChatManager import ChatManager

from conversation.ConversationRepository import ConversationRepository
from document.DocumentsRepository import DocumentsRepository
from embeddings.EmbeddingRepository import EmbeddingRepository
from message.MessageRepository import MessageRepository
from rights.CategoryRepository import CategoryRepository
from rights.UserRepository import UserRepository


class EmbeddingRepositoryProvider:
    def get_dependency(self) -> EmbeddingRepository:
        return EmbeddingRepository()


class DocumentDAOProvider:

    def get_dependency(self):
        return DocumentsRepository()


class ConversationDAOProvider:
    def get_dependency(self):
        return ConversationRepository()


class MessageDAOProvider:

    def get_dependency(self):
        return MessageRepository()


class ChatManagerProvider:
    def get_dependency(self) -> ChatManager:
        return ChatManager()


class CategoryDAOProvider:

    def get_dependency(self):
        return CategoryRepository()


class UserDAOProvider:

    def get_dependency(self):
        return UserRepository()


document_dao_provider = DocumentDAOProvider()
conversation_dao_provider = ConversationDAOProvider()
message_dao_provider = MessageDAOProvider()
category_dao_provider = CategoryDAOProvider()
user_dao_provider = UserDAOProvider()
