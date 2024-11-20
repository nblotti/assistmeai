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
from pydantic import BaseModel
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
    """
    Enum representing different tool names.

    This enumeration is used to define a set of constant values representing various tool names, each associated with a specific string identifier. It provides a standardized way to refer to and use different tools within the application.

    :ivar WEB_SEARCH: Represents the tool for web search operations.
    :vartype WEB_SEARCH: str
    :ivar GET_DATE: Represents the tool for getting the current date.
    :vartype GET_DATE: str
    :ivar SUMMARIZE: Represents the tool for summarizing content or data.
    :vartype SUMMARIZE: str
    :ivar TEMPLATE: Represents a general-purpose template tool.
    :vartype TEMPLATE: str
    """
    WEB_SEARCH = "web_search"
    GET_DATE = "get_date"
    SUMMARIZE = "summarize"
    TEMPLATE = "template"


class Slide(BaseModel):
    """
    Represents a single slide in a presentation.

    This class models the basic components of a slide including its title,
    content, and footer. It is a subclass of BaseModel, allowing it to
    interact seamlessly with other components of the presentation framework.

    :ivar title: The title of the slide.
    :type title: str
    :ivar content: The main content text of the slide.
    :type content: str
    :ivar footer: The footer text of the slide.
    :type footer: str
    """
    title: str
    content: str
    footer: str


class ToolManager:
    """
    Manages a collection of tools and provides access to them based on tool names.

    This class maintains a dictionary of tools, where each tool is a callable function.
    It provides methods to retrieve specific tools or all available tools.

    :ivar tools: A dictionary mapping tool names to their corresponding callables.
    :type tools: Dict[ToolName, Callable[..., str]]
    """

    def __init__(self):
        """
        Contains the initialization of the UtilityTools class and the mapping of tool names
        to their respective callables.

        Attributes
        ----------
        tools : Dict[ToolName, Callable[..., str]]
            A dictionary mapping each tool name to its callable function. This allows
            for dynamic invocation of the tool functions based on the tool name.
            Available tools are:
                - ToolName.WEB_SEARCH: links to the web_search function
                - ToolName.GET_DATE: links to the get_date function
                - ToolName.SUMMARIZE: links to the summarize function
                - ToolName.TEMPLATE: links to the template function
        """
        self.tools: Dict[ToolName, Callable[..., str]] = {

            ToolName.WEB_SEARCH: web_search,
            ToolName.GET_DATE: get_date,
            ToolName.SUMMARIZE: summarize,
            ToolName.TEMPLATE: template
        }

    def get_tools(self, tool_names: List[ToolName]) -> List[Callable[..., str]]:
        """
        Retrieves a list of callable tools based on specified tool names.

        This method takes a list of tool names and returns a list of corresponding callables
        from the `self.tools` dictionary. Each tool name in the input list is used to look up
        its corresponding callable in the `self.tools` dictionary, and these callables are
        compiled into a list which is then returned. The callables in the returned list can be
        invoked with the appropriate arguments as determined by their definitions.

        :param tool_names: A list of tool names to retrieve callables for.
        :type tool_names: List[ToolName]
        :return: A list of callables corresponding to the specified tool names.
        :rtype: List[Callable[..., str]]
        """
        return [self.tools[tool_name] for tool_name in tool_names]

    def get_all_tools(self) -> List[Callable[..., str]]:
        """
        ToolManager manages a collection of tools.

        This class allows addition, removal, and retrieval of tools.
        """
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
    """
    Asynchronous generator that yields database sessions.

    Iterates through the sessions retrieved from the database configuration
    and yields each session.

    :return: Yields database sessions.
    :rtype: AsyncGenerator
    """
    async for session in config.get_db():
        yield session


async def async_fetch_and_prepare_sessions():
    """
    Asynchronously fetches sessions from a database and appends each session to a list.

    This coroutine function iterates over the sessions fetched from the database,
    appending each session to the `db_sessions` list. The function returns the list of
    sessions after all sessions have been appended.

    :return: List of database sessions fetched.
    :rtype: list
    """
    db_sessions = []
    async for session in fetch_sessions():
        db_sessions.append(session)
    return db_sessions


def fetch_and_prepare_sessions_sync():
    """
    Fetch and prepare sessions synchronously.

    This function executes the asynchronous function `async_fetch_and_prepare_sessions`
    using `asyncio.run` to run it in a synchronous context.

    :return: The return value of the `async_fetch_and_prepare_sessions` function.
    :rtype: Any
    """
    return asyncio.run(async_fetch_and_prepare_sessions())


def get_document_text(document_manager: DocumentManager, document_id: int) -> str:
    """
    Extract the text content from a PDF document using given `document_manager` and `document_id`.

    :param document_manager: An instance of DocumentManager used to retrieve the PDF document.
    :type document_manager: DocumentManager
    :param document_id: The unique identifier of the document to be processed.
    :type document_id: int
    :return: The extracted text content from the PDF document.
    :rtype: str
    """
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

    document_manager = DocumentManager(DocumentsEmbeddingsRepository(sessions[0]), DocumentsRepository(sessions[0]),
                                       EmbeddingRepository())

    return get_document_text(document_manager, int(document_id))


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

    document_ids = [doc.document_id for doc in assistants_document]

    if not document_ids:
        return []

    docs: [] = document_manager.get_embeddings_by_ids(document_ids)
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
        logging.info(f'Too much token : {total_token}, defaulting to standard RAG')
        rag_retriever = CustomAzurePGVectorRetriever(QueryType.DOCUMENTS, ",".join(map(str, document_ids)), 10)
        docs = rag_retriever.invoke(query)
        return [LangChainDocument(page_content=doc.page_content, metadata=doc.metadata) for doc in docs]

    return documents
