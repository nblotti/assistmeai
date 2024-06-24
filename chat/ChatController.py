from typing import Annotated, List, Dict, Any

from fastapi import APIRouter, Query, Depends
from langchain.chains.llm import LLMChain
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain_core.prompts import PromptTemplate
from starlette.responses import JSONResponse

from DependencyManager import message_dao_provider, conversation_dao_provider
from chat.azure_openai import chat
from conversation.Conversation import Conversation
from conversation.ConversationRepository import ConversationRepository
from embeddings.CustomAzurePGVectorRetriever import CustomAzurePGVectorRetriever
from embeddings.EmbeddingsTools import QueryType
from memories.SqlMessageHistory import build_document_memory
from message.MessageRepository import MessageRepository
from vector_stores.postgres import build_specific_document_retriever, build_all_documents_retriever

chat_ai = APIRouter(
    prefix="/chat",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)
'''
------------------------------------------------------------------------------------------------------------------------

Command entry point

------------------------------------------------------------------------------------------------------------------------
'''

message_repository_dep = Annotated[MessageRepository, Depends(message_dao_provider.get_dependency)]
conversation_repository_dep = Annotated[ConversationRepository, Depends(conversation_dao_provider.get_dependency)]


@chat_ai.get("/command/")
async def message(message_repository: message_repository_dep, conversation_repository: conversation_repository_dep,
                  command: str, conversation_id: str, perimeter: str = Query(None)):
    # Get the current conversation and build document memory
    cur_conversation : Conversation = conversation_repository.get_conversation_by_id(conversation_id)
    memory = build_document_memory(message_repository, conversation_id)

    # Determine the appropriate retriever based on the perimeter or conversation PDF ID
    if perimeter:
        rag_retriever = CustomAzurePGVectorRetriever(QueryType.PERIMETER, perimeter)
    elif cur_conversation.pdf_id is not None and cur_conversation.pdf_id != 0:
        rag_retriever = CustomAzurePGVectorRetriever(QueryType.DOCUMENT, str(cur_conversation.pdf_id))
    else:
        rag_retriever = None

    # Choose the LLM chain
    if rag_retriever:
        chain = RetrievalQA.from_chain_type(
            llm=chat,
            verbose=True,
            retriever=rag_retriever,
            return_source_documents=True,
            output_key="result",
            memory=memory
        )
    else:
        # Load a simpler LLMChain without retriever
        template = """You are a chatbot having a conversation with a human.
        {chat_history}
        Human: {query}
        Chatbot:"""
        prompt = PromptTemplate(
            input_variables=["chat_history", "query"],
            template=template
        )
        chain = LLMChain(
            prompt=prompt,
            llm=chat,
            verbose=True,
            memory=memory,
            output_key="result"
        )

    # Invoke the chain with the command/query
    try:
        result = chain.invoke({"query": command})
        print(result)  # Or whatever logging mechanism you prefer
    except Exception as e:
        print(f"Error occurred: {e}")
        raise

    # Return response with results and possibly source metadata
    if "source_documents" in result:
        sources = [doc.metadata for doc in result["source_documents"]]
        return JSONResponse(content={"result": result["result"], "sources": sources})
    else:
        return JSONResponse(content={"result": result["result"]})
@chat_ai.get("/command/nomemory/")
async def message(conversation_repository: conversation_repository_dep, command: str, conversation_id: str,
                  perimeter: str = Query(...)):
    # Choose the LLM that will drive the agent
    # Only certain models support this
    cur_conversation = conversation_repository.get_conversation_by_id(conversation_id)

    if cur_conversation.pdf_id is None or cur_conversation.pdf_id == "-1":
        rag_retriever = CustomAzurePGVectorRetriever(QueryType.PERIMETER, perimeter)
    else:
        rag_retriever = CustomAzurePGVectorRetriever(QueryType.DOCUMENT, cur_conversation.pdf_id)

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
