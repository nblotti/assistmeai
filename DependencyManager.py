from ToolManager import ToolManager
from assistants.AssistantDocumentRepository import AssistantDocumentRepository
from assistants.AssistantsManager import AssistantManager
from assistants.AssistantsRepository import AssistantsRepository
from chat.ChatManager import ChatManager
from conversation.ConversationRepository import ConversationRepository
from document.DocumentManager import DocumentManager
from document.DocumentsRepository import DocumentsRepository
from embeddings.EmbeddingRepository import EmbeddingRepository
from message.MessageRepository import MessageRepository
from rights.CategoryRepository import CategoryRepository
from rights.UserRepository import UserRepository
from sharing.SharedGroupDocumentRepository import SharedGroupDocumentRepository
from sharing.SharedGroupRepository import SharedGroupRepository
from sharing.SharedGroupUserRepository import SharedGroupUserRepository


class EmbeddingRepositoryProvider:
    def get_dependency(self):
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


class SharedGroupRepositoryDAOProvider:

    def get_dependency(self):
        return SharedGroupRepository()


class SharedGroupUserRepositoryDAOProvider:

    def get_dependency(self):
        return SharedGroupUserRepository()


class SharedGroupDocumentRepositoryDAOProvider:

    def get_dependency(self):
        return SharedGroupDocumentRepository()


class AssistantDocumentRepositoryDAOProvider:

    def get_dependency(self):
        return AssistantDocumentRepository()


class DocumentManagerProvider:

    def __init__(self, document_repository: DocumentsRepository, embedding_repository: EmbeddingRepository):
        self.document_repository = document_repository
        self.embedding_repository = embedding_repository

    def get_dependency(self):
        return DocumentManager(self.document_repository, self.embedding_repository)


class AssistantManagerProvider:

    def __init__(self, message_repository: MessageRepository, assistants_repository: AssistantsRepository,
                 tool_manager: ToolManager):
        self.message_repository = message_repository
        self.assistants_repository = assistants_repository
        self.tool_manager = tool_manager

    def get_dependency(self):
        return AssistantManager(self.message_repository, self.assistants_repository, self.tool_manager)


class ToolManagerProvider:

    def get_dependency(self):
        return ToolManager()


tool_manager_provider = ToolManagerProvider()
