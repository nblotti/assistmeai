# ToolManager.py
import asyncio
import io
import logging
import os
import time
from datetime import datetime
from enum import Enum
from typing import Callable, Dict, List

import requests
import tiktoken
from duckduckgo_search import DDGS
from langchain_core.documents import Document
from langchain_core.tools import tool
from pydantic import BaseModel
from pypdf import PdfReader

import config
from assistants.AssistantDocumentRepository import AssistantDocumentRepository
from document.Document import LangChainDocument
from document.DocumentManager import DocumentManager
from document.DocumentsRepository import DocumentsRepository
from embeddings.CustomAzurePGVectorRetriever import CustomAzurePGVectorRetriever
from embeddings.QueryType import QueryType


class ToolName(str, Enum):
    """
    Enum representing different tool names.

    This enumeration is used to define a set of constant values representing various tool names, each associated with a specific string identifier. It provides a standardized way to refer to and use different tools within the application.

    :ivar WEB_SEARCH: Represents the tool for web search operations.
    :vartype WEB_SEARCH: str
    :ivar GET_DATE: Represents the tool for getting the current date.
    :vartype GET_DATE: str
    :ivar SEARCH_LIBRARY: Represents the tool for searching into user library.
    :vartype SEARCH_LIBRARY: str
    :ivar TEMPLATE: Represents a general-purpose template tool.
    :vartype TEMPLATE: str
    """
    WEB_SEARCH = "web_search"
    GET_DATE = "get_date"
    SEARCH_LIBRARY = "search_library"
    TEMPLATE = "template"
    FOCUS_ONLY = "focus_only"


class Slide(BaseModel):
    title: str
    content: str
    footer: str


class ToolManager:

    def __init__(self):
        self.tools: Dict[ToolName, Callable[..., str]] = {

            ToolName.WEB_SEARCH: web_search,
            ToolName.GET_DATE: get_date,
            ToolName.SEARCH_LIBRARY: search_library,
            ToolName.TEMPLATE: template,
            ToolName.FOCUS_ONLY: load_focus_only_document
        }

    def get_tools(self, tool_names: List[ToolName]) -> List[Callable[..., str]]:
        return [self.tools[tool_name] for tool_name in tool_names]

    def get_all_tools(self) -> List[Callable[..., str]]:
        return list(self.tools.values())


@tool
def web_search(query: str):
    """
    This tool is used to search web to have the latest information not present in the user library. Make sure to use
    it if you don't know the answer and that you didn't find it either in the users documents

    :param query: The search term(s) to be queried. Never more than 50 words !
    :return: The search results obtained from DuckDuckGo.
    """
    out = True
    loop = 0
    while out and loop <= 3:
        try:
            out = False
            loop += 1

            result = DDGS().text(query, max_results=5)
            return result
        except Exception as e:
            time.sleep(3)
            out = True
    return "no results"


@tool
def get_date() -> datetime:
    """This tool is useful to know the current date and time."""

    return datetime.now()


async def fetch_sessions():
    async for session in config.get_db():
        yield session


async def async_fetch_and_prepare_sessions():
    db_sessions = []
    async for session in fetch_sessions():
        db_sessions.append(session)
    return db_sessions


def fetch_and_prepare_sessions_sync():
    return asyncio.run(async_fetch_and_prepare_sessions())


def get_document_text(document_manager: DocumentManager, document_id: int) -> str:
    pdf_stream = document_manager.get_stream_by_id(document_id)
    pdf_reader = PdfReader(io.BytesIO(pdf_stream.document))
    text_content = ""
    for page in pdf_reader.pages:
        text_content += page.extract_text()
    return text_content


@tool
def template(document_id) -> []:
    """This tool is used to load a document content"""

    try:
        sessions = fetch_and_prepare_sessions_sync()
    except Exception as e:
        logging.error(f"Failed to fetch sessions: {e}")
        return "Error fetching sessions."

    if not sessions:
        logging.error("No repositories found.")
        return "Error: No repositories found."

    document_manager = DocumentManager(DocumentsRepository(sessions[0]))

    return get_document_text(document_manager, int(document_id))


@tool
def load_focus_only_document(document_id: str, ) -> List[LangChainDocument]:
    """This tool is used to load a focus only document content"""

    try:
        sessions = fetch_and_prepare_sessions_sync()
    except Exception as e:
        logging.error(f"Failed to fetch sessions: {e}")
        return []

    if not sessions:
        logging.error("No repositories found.")
        return []

    document_repository = EmbeddingRepository(sessions[0])

    document = document_repository.get_document_by_id(int(document_id))


    rag_retriever = CustomAzurePGVectorRetriever(QueryType.DOCUMENT,  document_id, -1)
    docs = rag_retriever.invoke(query)
    documents: list[LangChainDocument] = []
    for document in docs:
        current_doc = LangChainDocument(
            page_content=document.page_content,
            metadata=document.metadata
        )
        documents.append(current_doc)
    encoding = tiktoken.get_encoding("o200k_base")

    total_token: int = 0

    for document in documents:
        total_token += len(encoding.encode(document.model_dump_json()))

    if total_token > 100000:
        logging.info(f'Too much token : {total_token}, defaulting to standard RAG')
        rag_retriever = CustomAzurePGVectorRetriever(QueryType.DOCUMENTS, ",".join(map(str, document_ids)), 10)
        docs = rag_retriever.invoke(query)
        return [LangChainDocument(page_content=doc.page_content, metadata=doc.metadata) for doc in docs]

    return documents


@tool
def search_library(assistant_id: str, query: str) -> List[LangChainDocument]:
    """This tool is used to search documents in the user's library."""

    try:
        sessions = fetch_and_prepare_sessions_sync()
    except Exception as e:
        logging.error(f"Failed to fetch sessions: {e}")
        return []

    if not sessions:
        logging.error("No repositories found.")
        return []

    assistant_document_manager = AssistantDocumentRepository(sessions[0])

    logging.debug("Assistant id: %s", assistant_id)
    assistants_document = assistant_document_manager.list_by_assistant_id(int(assistant_id))

    document_ids = [doc.document_id for doc in assistants_document]

    if not document_ids:
        return []

    rag_retriever = CustomAzurePGVectorRetriever(QueryType.DOCUMENTS, ",".join(map(str, document_ids)), -1)
    docs = rag_retriever.invoke(query)
    documents: list[LangChainDocument] = []
    for document in docs:
        current_doc = LangChainDocument(
            page_content=document.page_content,
            metadata=document.metadata
        )
        documents.append(current_doc)
    encoding = tiktoken.get_encoding("o200k_base")

    total_token: int = 0

    for document in documents:
        total_token += len(encoding.encode(document.model_dump_json()))

    if total_token > 100000:
        logging.info(f'Too much token : {total_token}, defaulting to standard RAG')
        rag_retriever = CustomAzurePGVectorRetriever(QueryType.DOCUMENTS, ",".join(map(str, document_ids)), 10)
        docs = rag_retriever.invoke(query)
        return [LangChainDocument(page_content=doc.page_content, metadata=doc.metadata) for doc in docs]

    return documents
