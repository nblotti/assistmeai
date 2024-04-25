import logging

from langchain.tools.retriever import create_retriever_tool
from langchain_community.retrievers.wikipedia import WikipediaRetriever
from langchain_core.tools import Tool

from chat.Conversation import Conversation
from vector_stores.pinecone import build_all_documents_retriever, build_specific_document_retriever



def get_document_retreiver(cur_conversation : Conversation, perimeter : list[str] ):
    if cur_conversation.pdf_id is None or cur_conversation.pdf_id == "-1":
        retriever = build_all_documents_retriever(perimeter)
    else:
        retriever = build_specific_document_retriever(cur_conversation.pdf_id)

    return create_retriever_tool(
        retriever,
        "document_search",
        "For any questions, you must first use this tool!",
    )

def get_wikipedia_retreiver():
    retriever = WikipediaRetriever()
    return create_retriever_tool(
        retriever,
        "wikipedia_search",
        "Only  use this tool if you found no information using other tools ! ",
    )
