from embeddings.EmbeddingRepository import EmbeddingRepository
from pdf.PdfManager import PdfManager
from pdf.SqliteDAO import SqliteDAO


class EmbeddingRepositoryProvider:

    def get_dependency(self) -> EmbeddingRepository:
        return EmbeddingRepository()


class SqliteDAOProvider:
    def get_dependency(self):
        return SqliteDAO()


# Define an outer dependency provider class
class PdfManagerProvider:
    def __init__(self, embedding_repository_provider: EmbeddingRepositoryProvider,
                 sqlite_dao_provider: SqliteDAOProvider):
        self.embedding_repositoryProvider = embedding_repository_provider
        self.sqlite_dao_provider = sqlite_dao_provider

    def get_dependency(self) -> PdfManager:
        embedding_repository = self.embedding_repositoryProvider.get_dependency()
        sqlite_dao = self.sqlite_dao_provider.get_dependency()
        return PdfManager(embedding_repository,sqlite_dao)

