from assistants.AssistantsRepository import AssistantsRepository
from chat.ChatManager import ChatManager

from conversation.ConversationRepository import ConversationRepository
from document.DocumentsRepository import DocumentsRepository
from embeddings.EmbeddingRepository import EmbeddingRepository
from message.MessageRepository import MessageRepository
from rights.CategoryRepository import CategoryRepository
from rights.UserRepository import UserRepository
from sharing.GroupRepository import GroupRepository
from sharing.DocumentShareRepository import DocumentShareRepository


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


class AssistantsDAOProvider:

    def get_dependency(self):
        return AssistantsRepository()


class GroupRepositoryDAOProvider:

    def get_dependency(self):
        return GroupRepository()


class DocumentShareRepositoryDAOProvider:

    def get_dependency(self):
        return DocumentShareRepository()


document_dao_provider = DocumentDAOProvider()
conversation_dao_provider = ConversationDAOProvider()
message_dao_provider = MessageDAOProvider()
category_dao_provider = CategoryDAOProvider()
user_dao_provider = UserDAOProvider()
assistants_dao_provider = AssistantsDAOProvider()
group_dao_provider = GroupRepositoryDAOProvider()
document_share_dao_provider = DocumentShareRepositoryDAOProvider()
