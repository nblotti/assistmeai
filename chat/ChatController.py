from typing import Annotated

from fastapi import APIRouter, Query, Depends, HTTPException
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableWithMessageHistory
from starlette.responses import JSONResponse

from ProviderManager import message_dao_provider, conversation_dao_provider, document_manager_provider
from chat.azure_openai import chat_gpt_4o_mini
from conversation.Conversation import ConversationCreate
from conversation.ConversationRepository import ConversationRepository
from document.DocumentManager import DocumentManager
from embeddings.CustomAzurePGVectorRetriever import CustomAzurePGVectorRetriever
from embeddings.EmbeddingsTools import QueryType
from memories.SqlMessageHistory import build_agent_memory
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

message_repository_dep = Annotated[MessageRepository, Depends(message_dao_provider)]
conversation_repository_dep = Annotated[ConversationRepository, Depends(conversation_dao_provider)]
document_manager_dep = Annotated[DocumentManager, Depends(document_manager_provider)]


def format_docs(docs):
    return [doc.metadata for doc in docs]


@chat_ai.get("/command/")
async def message(message_repository: message_repository_dep, conversation_repository: conversation_repository_dep,
                  command: str, conversation_id: str, perimeter: str = Query(None)):
    # Get the current conversation and build document memory
    cur_conversation: ConversationCreate = conversation_repository.get_conversation_by_id(int(conversation_id))
    memory = build_agent_memory(message_repository, conversation_id)

    # Determine the appropriate retriever based on the perimeter or conversation PDF ID
    if cur_conversation.pdf_id is not None and cur_conversation.pdf_id != 0:
        rag_retriever = CustomAzurePGVectorRetriever(QueryType.DOCUMENT, str(cur_conversation.pdf_id))
    elif perimeter:
        rag_retriever = CustomAzurePGVectorRetriever(QueryType.PERIMETER, perimeter)
    else:
        raise HTTPException(status_code=400, detail="Invalid argument: perimeter cannot be null")

    system_prompt = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer "
        "the question. If you don't know the answer, say that you "
        "don't know. Use three sentences maximum and keep the "
        "answer concise."
        "\n\n"
        "{context}"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )

    # This Runnable takes a dict with keys 'input' and 'context',
    # formats them into a prompt, and generates a response.
    rag_chain_from_docs = (
            {
                "input": lambda x: x["input"],  # input query
                "context": lambda x: format_docs(x["context"]),  # context
            }
            | prompt  # format query and context into prompt
            | chat_gpt_4o_mini  # generate response
            | StrOutputParser()  # coerce to string
    )

    # Pass input query to retriever
    retrieve_docs = (lambda x: x["input"]) | rag_retriever

    # Below, we chain `.assign` calls. This takes a dict and successively
    # adds keys-- "context" and "answer"-- where the value for each key
    # is determined by a Runnable. The Runnable operates on all existing
    # keys in the dict.
    rag_chain = RunnablePassthrough.assign(context=retrieve_docs).assign(
        answer=rag_chain_from_docs,
    )
    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        lambda session_id: memory,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )
    # Invoke the chain with the command/query
    try:
        # result = chain.invoke({"query": command})

        result = conversational_rag_chain.invoke({"input": command}, {"configurable": {"session_id": "unused"}})
        # print(result)  # Or whatever logging mechanism you prefer
    except Exception as e:
        print(f"Error occurred: {e}")
        raise

    # Return response with results and possibly source metadata
    if "context" in result:
        sources = [doc.metadata for doc in result["context"]]
        return JSONResponse(content={"result": result["answer"], "sources": sources})
    else:
        return JSONResponse(content={"result": result["answer"]})


@chat_ai.get("/summarize/{blob_id}/")
async def summarize(document_manager: document_manager_dep, blob_id: str):
    return await document_manager.summarize(blob_id)
