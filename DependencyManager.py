import logging
import os

import tiktoken
from langchain_community.tools import DuckDuckGoSearchResults, DuckDuckGoSearchRun
from langchain_core.tools import tool

from assistants.AssistantDocumentRepository import AssistantDocumentRepository
from assistants.AssistantsManager import AssistantManager
from assistants.AssistantsRepository import AssistantsRepository
from chat.ChatManager import ChatManager
from conversation.ConversationRepository import ConversationRepository
from document import Document
from document.DocumentManager import DocumentManager
from document.DocumentsRepository import DocumentsRepository
from embeddings.CustomAzurePGVectorRetriever import CustomAzurePGVectorRetriever
from embeddings.EmbeddingRepository import EmbeddingRepository
from embeddings.EmbeddingsTools import QueryType
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

    def __init__(self, message_repository: MessageRepository, assistants_repository: AssistantsRepository):
        self.message_repository = message_repository
        self.assistants_repository = assistants_repository

    def get_dependency(self):
        return AssistantManager(self.message_repository, self.assistants_repository, full_tools, no_doc_tools)


@tool
def summarize(assistant_id: str, query: str) -> str:
    """This tool is used to search into documents in the user's library."""
    document_manager = document_manager_provider.get_dependency()
    assistant_document_manager = assistant_document_dao_provider.get_dependency()
    logging.debug("Assistant id: %s", assistant_id)
    assistants_document = assistant_document_manager.list_by_assistant_id(assistant_id)

    ids = [num.document_id for num in assistants_document]

    if len(ids) == 0:
        return "No documents found"

    documents: [str] = document_manager.get_embeddings_by_ids(ids)

    encoding = tiktoken.encoding_for_model(os.environ["AZURE_OPENAI_EMBEDDINGS_MODEL_VERSION"])

    total_token: int = 0

    for document in documents:
        total_token += len(encoding.encode(document[0]))

    if total_token > 16384:
        logging.info("-------------------------------------------------------")
        logging.info(f'Too much token : {total_token}, defaulting to standard RAG')
        logging.info("-------------------------------------------------------")
        documents = ""
        rag_retriever = CustomAzurePGVectorRetriever(QueryType.DOCUMENTS, ",".join(ids))
        results: [Document] = rag_retriever.invoke(query)
        documents = [result.metadata.get("text") for result in results]
        total_token = 0
        for document in documents:
            total_token += len(encoding.encode(document[0]))

    logging.info("-------------------------------------------------------")
    logging.info(f'Number of token : {total_token}')
    logging.info("-------------------------------------------------------")

    return documents


@tool
def web_search(query: str) -> DuckDuckGoSearchResults:
    """This tool is used to search web to have the latest information not present in the user library. Make sure to use
    it if you don't know the answer and that you didn't find it either in the users documents"""
    search = DuckDuckGoSearchRun()

    return search.invoke(query)


@tool
def get_date(location: str = "Switzerland") -> DuckDuckGoSearchResults:
    """This tool is useful to know the current date and time. Make sur to use it for all question where you need to know
    the current date and time."""
    search = DuckDuckGoSearchRun()
    query = f'what time is it in {location}'
    return search.invoke(query)


full_tools = [get_date, web_search, summarize]
no_doc_tools = [get_date, web_search]

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
assistant_document_dao_provider = AssistantDocumentRepositoryDAOProvider()
assistant_manager_provider = AssistantManagerProvider(message_dao_provider.get_dependency(),
                                                      assistants_dao_provider.get_dependency())
