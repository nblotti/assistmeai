from typing import Annotated

from fastapi import APIRouter, Query, Depends, HTTPException
from langchain.chains.retrieval_qa.base import RetrievalQA
from starlette.responses import JSONResponse

from DependencyManager import message_dao_provider, conversation_dao_provider, document_manager_provider
from chat.azure_openai import chat_gpt_35
from conversation.Conversation import Conversation
from conversation.ConversationRepository import ConversationRepository
from document.DocumentManager import DocumentManager
from embeddings.CustomAzurePGVectorRetriever import CustomAzurePGVectorRetriever
from embeddings.EmbeddingsTools import QueryType
from memories.SqlMessageHistory import build_memory
from message.MessageRepository import MessageRepository

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
document_manager_dep = Annotated[DocumentManager, Depends(document_manager_provider.get_dependency)]


@chat_ai.get("/command/")
async def message(message_repository: message_repository_dep, conversation_repository: conversation_repository_dep,
                  command: str, conversation_id: str, perimeter: str = Query(None)):
    # Get the current conversation and build document memory
    cur_conversation: Conversation = conversation_repository.get_conversation_by_id(conversation_id)
    memory = build_memory(message_repository, conversation_id)

    # Determine the appropriate retriever based on the perimeter or conversation PDF ID
    if cur_conversation.pdf_id is not None and cur_conversation.pdf_id != 0:
        rag_retriever = CustomAzurePGVectorRetriever(QueryType.DOCUMENT, str(cur_conversation.pdf_id))
    elif perimeter:
        rag_retriever = CustomAzurePGVectorRetriever(QueryType.PERIMETER, perimeter)
    else:
        raise HTTPException(status_code=400, detail="Invalid argument: perimeter cannot be null")

    # Choose the LLM chain
    if rag_retriever:
        chain = RetrievalQA.from_chain_type(
            llm=chat_gpt_35,
            # verbose=True,
            retriever=rag_retriever,
            return_source_documents=True,
            output_key="result",
            memory=memory
        )

    # Invoke the chain with the command/query
    try:
        result = chain.invoke({"query": command})
        # print(result)  # Or whatever logging mechanism you prefer
    except Exception as e:
        print(f"Error occurred: {e}")
        raise

    # Return response with results and possibly source metadata
    if "source_documents" in result:
        sources = [doc.metadata for doc in result["source_documents"]]
        return JSONResponse(content={"result": result["result"], "sources": sources})
    else:
        return JSONResponse(content={"result": result["result"]})


@chat_ai.get("/summarize/{blob_id}/")
async def summarize(document_manager: document_manager_dep, blob_id: str):
    return await document_manager.summarize(blob_id)
