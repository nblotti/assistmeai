import logging
import os

import tiktoken
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.documents import Document
from langchain_core.tools import ToolException
from langchain_core.tools import tool

from DependencyManager import document_manager_provider, assistant_document_dao_provider
from embeddings.CustomAzurePGVectorRetriever import CustomAzurePGVectorRetriever
from embeddings.EmbeddingsTools import QueryType


def _handle_error(error: ToolException) -> str:
    print("-------------------------------------------------------")
    print("-------------------------------------------------------")
    print(f"Error : {error}")
    print("-------------------------------------------------------")
    print("-------------------------------------------------------")
    return f"The following errors occurred during tool execution: `{error.args[0]}`"


@tool
def summarize(assistant_id: str, query: str):
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
def web_search(query: str):
    """This tool is used to search web to have the latest information not present in the user library. Make sure to use
    it if you don't know the answer and that you didn't find it either in the users documents"""
    search = DuckDuckGoSearchRun()

    return search.invoke(query)


@tool
def get_date(location: str = "Switzerland"):
    """This tool is useful to know the current date and time. Make sur to use it for all question where you need to know
    the current date and time."""
    search = DuckDuckGoSearchRun()
    query = f'what time is it in {location}'
    return search.invoke(query)
