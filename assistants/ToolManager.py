# ToolManager.py
import asyncio
import io
import logging
import os
import time
from datetime import datetime
from enum import Enum
from typing import Callable, Dict, List

import tiktoken
from duckduckgo_search import DDGS
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from pypdf import PdfReader

import config
from assistants.AssistantDocumentRepository import AssistantDocumentRepository
from document.Document import LangChainDocument
from document.DocumentManager import DocumentManager
from document.DocumentsRepository import DocumentsRepository
from embeddings.CustomAzurePGVectorRetriever import CustomAzurePGVectorRetriever
from embeddings.DocumentsEmbeddingsRepository import DocumentsEmbeddingsRepository
from embeddings.EmbeddingRepository import EmbeddingRepository
from embeddings.EmbeddingsTools import QueryType


class ToolName(str, Enum):
    WEB_SEARCH = "web_search"
    GET_DATE = "get_date"
    SUMMARIZE = "summarize"
    POWERPOINT = "powerpoint"
    TEMPLATE = "template"


class Slide(BaseModel):
    title: str
    content: str
    footer: str


class ToolManager:
    def __init__(self):
        self.tools: Dict[ToolName, Callable[..., str]] = {

            ToolName.WEB_SEARCH: web_search,
            ToolName.GET_DATE: get_date,
            ToolName.SUMMARIZE: summarize,
            ToolName.POWERPOINT: powerpoint,
            ToolName.TEMPLATE: template
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


class CalculatorInput(BaseModel):
    a: list[Slide] = Field(description="The list of slides")


@tool(args_schema=CalculatorInput, return_direct=True)
def powerpoint(a) -> []:
    """This tool is used to create a PowerPoint based on a content provided and a query. The footer contains the page number (provide it) on the right"""

    logging.info(a)
    return a


async def fetch_sessions():
    async for session in config.get_db():
        yield session


async def async_fetch_and_prepare_sessions():
    sessions = []
    async for session in fetch_sessions():
        sessions.append(session)
    return sessions


def fetch_and_prepare_sessions_sync():
    return asyncio.run(async_fetch_and_prepare_sessions())


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

    document_manager = DocumentManager(DocumentsEmbeddingsRepository(sessions[0]), DocumentsRepository(sessions[0]),
                                       EmbeddingRepository())

    pdf_stream = document_manager.get_stream_by_id(int(document_id))

    pdf_reader = PdfReader(io.BytesIO(pdf_stream.document))
    text_content = ""

    for page_num in range(len(pdf_reader.pages)):
        text_content += pdf_reader.pages[page_num].extract_text()

    return text_content


@tool
def summarize(assistant_id: str, query: str) -> List[LangChainDocument]:
    """This tool is used to search into documents in the user's library."""

    try:
        sessions = fetch_and_prepare_sessions_sync()
    except Exception as e:
        logging.error(f"Failed to fetch sessions: {e}")
        return []

    if not sessions:
        logging.error("No repositories found.")
        return []

    assistant_document_manager = AssistantDocumentRepository(sessions[0])
    document_manager = DocumentManager(DocumentsEmbeddingsRepository(sessions[0]), DocumentsRepository(sessions[0]),
                                       EmbeddingRepository())
    logging.debug("Assistant id: %s", assistant_id)
    assistants_document = assistant_document_manager.list_by_assistant_id(int(assistant_id))

    ids = [num.document_id for num in assistants_document]

    if len(ids) == 0:
        return []

    docs: [] = document_manager.get_embeddings_by_ids(ids)
    documents: list[LangChainDocument] = []
    for document in docs:
        current_doc = LangChainDocument(
            page_content=document[0],
            metadata=document[1]
        )
        documents.append(current_doc)
    encoding = tiktoken.encoding_for_model(os.environ["AZURE_OPENAI_EMBEDDINGS_MODEL_VERSION"])

    total_token: int = 0

    for document in documents:
        total_token += len(encoding.encode(document.model_dump_json()))

    if total_token > 100000:
        documents = []
        logging.info("-------------------------------------------------------")
        logging.info(f'Too much token : {total_token}, defaulting to standard RAG')
        logging.info("-------------------------------------------------------")
        rag_retriever = CustomAzurePGVectorRetriever(QueryType.DOCUMENTS, ",".join(ids), 10)
        doc = rag_retriever.invoke(query)
        for document in doc:
            current_doc = LangChainDocument(
                page_content=document.page_content,
                metadata=document.metadata
            )
            documents.append(current_doc)
    return documents
