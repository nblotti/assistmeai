from document.DocumentManager import DocumentManager
from chat.ChatManager import ChatManager
from document.DocumentsRepository import DocumentsRepository
from embeddings.DocumentsEmbeddingsRepository import DocumentsEmbeddingsRepository
from embeddings.EmbeddingRepository import EmbeddingRepository
from rights.CategoryRepository import CategoryRepository
from rights.UserRepository import UserRepository
from sharing.SharedGroupDocumentRepository import SharedGroupDocumentRepository
from sharing.SharedGroupRepository import SharedGroupRepository
from sharing.SharedGroupUserRepository import SharedGroupUserRepository


class EmbeddingRepositoryProvider:
    def get_dependency(self):
        return EmbeddingRepository()


class DocumentsEmbeddingsDAOProvider:

    def get_dependency(self):
        return DocumentsEmbeddingsRepository()


class ChatManagerProvider:
    def get_dependency(self) -> ChatManager:
        return ChatManager()


class CategoryDAOProvider:

    def get_dependency(self):
        return CategoryRepository()


class UserDAOProvider:

    def get_dependency(self):
        return UserRepository()


class SharedGroupRepositoryDAOProvider:

    def get_dependency(self):
        return SharedGroupRepository()


class SharedGroupUserRepositoryDAOProvider:

    def get_dependency(self):
        return SharedGroupUserRepository()


class SharedGroupDocumentRepositoryDAOProvider:

    def get_dependency(self):
        return SharedGroupDocumentRepository()


class DocumentManagerProvider:

    def __init__(self, document_embeddings_repository: DocumentsEmbeddingsRepository,
                 document_repository: DocumentsRepository, embedding_repository: EmbeddingRepository):
        self.document_embeddings_repository = document_embeddings_repository;
        self.document_repository = document_repository
        self.embedding_repository = embedding_repository

    def get_dependency(self):
        return DocumentManager(self.document_embeddings_repository, self.document_repository, self.embedding_repository)
