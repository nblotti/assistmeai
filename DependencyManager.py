from embeddings.DocumentsEmbeddingsRepository import DocumentsEmbeddingsRepository
from embeddings.EmbeddingRepository import EmbeddingRepository
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
