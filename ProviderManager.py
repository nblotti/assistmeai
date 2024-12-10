from fastapi import Depends
from requests import Session

from assistants.AssistantDocumentRepository import AssistantDocumentRepository
from assistants.AssistantsManager import AssistantManager
from assistants.AssistantsRepository import AssistantsRepository
from assistants.ToolManager import ToolManager
from config import get_db
from conversation.ConversationRepository import ConversationRepository
from document.DocumentCategoryRepository import DocumentCategoryRepository
from document.DocumentManager import DocumentManager
from document.DocumentsRepository import DocumentsRepository
from embeddings.DocumentsEmbeddingsRepository import DocumentsEmbeddingsRepository
from job.JobRepository import JobRepository
from message.MessageRepository import MessageRepository
from rights.UserManager import UserManager
from rights.UserRepository import UserRepository
from sharing.SharedGroupDocumentRepository import SharedGroupDocumentRepository
from sharing.SharedGroupRepository import SharedGroupRepository
from sharing.SharedGroupUserRepository import SharedGroupUserRepository


def user_dao_provider(session: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(session)


def shared_group_user_dao_provider(session: Session = Depends(get_db)) -> SharedGroupUserRepository:
    return SharedGroupUserRepository(session)


def shared_group_dao_provider(session: Session = Depends(get_db)) -> SharedGroupRepository:
    return SharedGroupRepository(session)


def share_group_document_dao_provider(session: Session = Depends(get_db)) -> SharedGroupDocumentRepository:
    return SharedGroupDocumentRepository(session)


def category_dao_provider(session: Session = Depends(get_db)) -> DocumentCategoryRepository:
    return DocumentCategoryRepository(session)


def conversation_dao_provider(session: Session = Depends(get_db)) -> ConversationRepository:
    return ConversationRepository(session)


def message_dao_provider(session: Session = Depends(get_db)) -> MessageRepository:
    return MessageRepository(session)


def document_dao_provider(session: Session = Depends(get_db)) -> DocumentsRepository:
    return DocumentsRepository(session)


def job_dao_provider(session: Session = Depends(get_db)) -> JobRepository:
    return JobRepository(session)


def document_manager_provider(session: Session = Depends(get_db)) -> DocumentManager:
    return DocumentManager(DocumentsEmbeddingsRepository(session),
                           DocumentsRepository(session))


def user_manager_provider(session: Session = Depends(get_db)) -> UserManager:
    return UserManager(user_dao_provider(session),
                       category_dao_provider(session),
                       document_manager_provider(session))


def assistant_document_dao_provider(session: Session = Depends(get_db)) -> AssistantDocumentRepository:
    return AssistantDocumentRepository(session)


def assistant_manager_provider(session: Session = Depends(get_db)) -> AssistantManager:
    return AssistantManager(message_dao_provider(session), AssistantsRepository(session), ToolManager())
