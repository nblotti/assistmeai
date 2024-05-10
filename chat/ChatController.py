from typing import Annotated

from fastapi import APIRouter, Query, Depends
from fastapi import Response
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain_openai import ChatOpenAI

from DependencyManager import message_dao_provider, conversation_dao_provider
from conversation.ConversationRepository import ConversationRepository
from embeddings.CustomPineconeRetriever import CustomPineconeRetriever, QueryType
from memories.SqlMessageHistory import build_document_memory
from message.MessageRepository import MessageRepository

chat_ai = APIRouter(
    prefix="/chat",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)

chat = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, verbose=True)


'''
------------------------------------------------------------------------------------------------------------------------

Command entry point

------------------------------------------------------------------------------------------------------------------------
'''

message_repository_dep = Annotated[MessageRepository, Depends(message_dao_provider.get_dependency)]
conversation_repository_dep = Annotated[ConversationRepository, Depends(conversation_dao_provider.get_dependency)]

@chat_ai.get("/command/")
async def message(message_repository: message_repository_dep, conversation_repository: conversation_repository_dep,
                  command: str, conversation_id: str, perimeter: str = Query(...)):
    # Choose the LLM that will drive the agent
    # Only certain models support this
    cur_conversation = conversation_repository.get_conversation_by_id(conversation_id)

    memory = build_document_memory(message_repository, conversation_id)

    if cur_conversation.pdf_id is None or cur_conversation.pdf_id == "-1":
        rag_retriever = CustomPineconeRetriever(QueryType.PERIMETER, perimeter)
    else:
        rag_retriever = CustomPineconeRetriever(QueryType.DOCUMENT, cur_conversation.pdf_id)

    chain = RetrievalQA.from_chain_type(
        llm=chat,
        verbose=True,
        retriever=rag_retriever,
        return_source_documents=True,
        memory=memory
    )

    result = chain.invoke({"query": command})
    sources = []
    for document in result["source_documents"]:
        sources.append(document.metadata)

    return {"result": result["result"], "sources": sources}


@chat_ai.get("/command/nomemory/")
async def message(conversation_repository: conversation_repository_dep, command: str, conversation_id: str,
                  perimeter: str = Query(...)):
    # Choose the LLM that will drive the agent
    # Only certain models support this
    cur_conversation = conversation_repository.get_conversation_by_id(conversation_id)

    if cur_conversation.pdf_id is None or cur_conversation.pdf_id == "-1":
        rag_retriever = CustomPineconeRetriever(QueryType.PERIMETER, perimeter)
    else:
        rag_retriever = CustomPineconeRetriever(QueryType.DOCUMENT, cur_conversation.pdf_id)

    chain = RetrievalQA.from_chain_type(
        llm=chat,
        verbose=True,
        retriever=rag_retriever,
        return_source_documents=True,
    )

    result = chain.invoke({"query": command})
    sources = []
    for document in result["source_documents"]:
        sources.append(document.metadata)

    return {"result": result["result"], "sources": sources}
