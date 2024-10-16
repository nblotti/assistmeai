from fastapi import Depends
from requests import Session

from DependencyManager import CategoryDAOProvider, \
    UserDAOProvider, SharedGroupRepositoryDAOProvider, SharedGroupUserRepositoryDAOProvider, \
    SharedGroupDocumentRepositoryDAOProvider, EmbeddingRepositoryProvider, DocumentsEmbeddingsDAOProvider
from ToolManager import ToolManager
from assistants.AssistantDocumentRepository import AssistantDocumentRepository
from assistants.AssistantsManager import AssistantManager
from assistants.AssistantsRepository import AssistantsRepository
from config import get_db
from conversation.ConversationRepository import ConversationRepository
from document.DocumentManager import DocumentManager
from document.DocumentsRepository import DocumentsRepository
from message.MessageRepository import MessageRepository

document_embeddings_dao_provider = DocumentsEmbeddingsDAOProvider()
category_dao_provider = CategoryDAOProvider()
user_dao_provider = UserDAOProvider()
shared_group_dao_provider = SharedGroupRepositoryDAOProvider()
shared_group_user_dao_provider = SharedGroupUserRepositoryDAOProvider()
share_group_document_dao_provider = SharedGroupDocumentRepositoryDAOProvider()
embeddings_dao_provider = EmbeddingRepositoryProvider()


def conversation_dao_provider(session: Session = Depends(get_db)) -> ConversationRepository:
    return ConversationRepository(session)


def message_dao_provider(session: Session = Depends(get_db)) -> MessageRepository:
    return MessageRepository(session)


def document_dao_provider(session: Session = Depends(get_db)) -> DocumentsRepository:
    return DocumentsRepository(session)


def document_manager_provider(session: Session = Depends(get_db)) -> DocumentManager:
    return DocumentManager(document_embeddings_dao_provider.get_dependency(),
                           DocumentsRepository(session),
                           embeddings_dao_provider.get_dependency())


def assistant_document_dao_provider(session: Session = Depends(get_db)) -> AssistantDocumentRepository:
    return AssistantDocumentRepository(session)


def assistant_manager_provider(session: Session = Depends(get_db)) -> AssistantManager:
    return AssistantManager(MessageRepository(session), AssistantsRepository(session), ToolManager())
