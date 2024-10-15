from fastapi import Depends
from requests import Session

from DependencyManager import DocumentDAOProvider, ConversationDAOProvider, MessageDAOProvider, CategoryDAOProvider, \
    UserDAOProvider, AssistantsDAOProvider, SharedGroupRepositoryDAOProvider, SharedGroupUserRepositoryDAOProvider, \
    SharedGroupDocumentRepositoryDAOProvider, EmbeddingRepositoryProvider, DocumentManagerProvider, \
    AssistantManagerProvider, tool_manager_provider
from assistants.AssistantDocumentRepository import AssistantDocumentRepository
from config import get_db

document_dao_provider = DocumentDAOProvider()
conversation_dao_provider = ConversationDAOProvider()
message_dao_provider = MessageDAOProvider()
category_dao_provider = CategoryDAOProvider()
user_dao_provider = UserDAOProvider()
assistants_dao_provider = AssistantsDAOProvider()
shared_group_dao_provider = SharedGroupRepositoryDAOProvider()
shared_group_user_dao_provider = SharedGroupUserRepositoryDAOProvider()
share_group_document_dao_provider = SharedGroupDocumentRepositoryDAOProvider()
embeddings_dao_provider = EmbeddingRepositoryProvider()
document_manager_provider = DocumentManagerProvider(document_dao_provider.get_dependency(),
                                                    embeddings_dao_provider.get_dependency())


def assistant_document_dao_provider(session: Session = Depends(get_db)) -> AssistantDocumentRepository:
    return AssistantDocumentRepository(session)


assistant_manager_provider = AssistantManagerProvider(message_dao_provider.get_dependency(),
                                                      assistants_dao_provider.get_dependency(),
                                                      tool_manager_provider.get_dependency())
