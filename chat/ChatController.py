import asyncio
import logging
import os
import uuid
from typing import Annotated

from fastapi import APIRouter, Query, Depends, HTTPException
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_text_splitters import CharacterTextSplitter
from pydantic.v1 import BaseModel, Field
from starlette.responses import JSONResponse

from DependencyManager import message_dao_provider, conversation_dao_provider
from chat.azure_openai import chat_gpt_35, chat_gpt_4o
from conversation.Conversation import Conversation
from conversation.ConversationRepository import ConversationRepository
from document.DocumentsController import embeddings_repository_dep, document_repository_dep
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


@chat_ai.get("/command/")
async def message(message_repository: message_repository_dep, conversation_repository: conversation_repository_dep,
                  command: str, conversation_id: str, perimeter: str = Query(None)):
    # Get the current conversation and build document memory
    cur_conversation: Conversation = conversation_repository.get_conversation_by_id(conversation_id)
    memory = build_memory(message_repository, conversation_id)

    # Determine the appropriate retriever based on the perimeter or conversation PDF ID
    if perimeter:
        rag_retriever = CustomAzurePGVectorRetriever(QueryType.PERIMETER, perimeter)
    elif cur_conversation.pdf_id is not None and cur_conversation.pdf_id != 0:
        rag_retriever = CustomAzurePGVectorRetriever(QueryType.DOCUMENT, str(cur_conversation.pdf_id))
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


class Topic(BaseModel):
    name: str = Field(description=" The name of the topic that will be summarized")


class DocumentSummary(BaseModel):
    content: str = Field(description="The list of topic that have been summarized in the document")


@tool("summary-tool")
def summarize_tool(topic: Topic, summary: DocumentSummary):
    """This tool is used to write a concise summary of each topic in the input"""
    logging.debug("{topic} {summary}")
    return topic, summary


@chat_ai.get("/summarize/{blob_id}/")
async def summarize(documents_repository: document_repository_dep, embedding_repository: embeddings_repository_dep,
                    blob_id: str):
    content = documents_repository.get_by_id(blob_id)
    if not content:
        raise HTTPException(status_code=404, detail="Document not found")

    path = "./" + str(uuid.uuid4())
    temp_pdf_file = path + ".pdf"

    with open(temp_pdf_file, "wb") as file_w:
        file_w.write(content[1])

    loader = PyPDFLoader(temp_pdf_file)
    pages = loader.load()

    text_splitter = CharacterTextSplitter(separator="\n", chunk_size=3000, chunk_overlap=500, length_function=len)
    split_docs = text_splitter.split_documents(pages)

    tools = [summarize_tool]

    llm_with_tools = chat_gpt_4o.bind_tools(tools)

    tasks = [llm_with_tools.ainvoke(doc.page_content) for doc in split_docs[:2]]
    results = await asyncio.gather(*tasks)

    try:
        os.remove(temp_pdf_file)
        print(f"File '{temp_pdf_file}' deleted successfully.")
    except OSError as e:
        print(f"Error deleting file '{temp_pdf_file}': {e}")

    messages = [SystemMessage("Given the results of a series of tool call, Your task is to format the responses."
                              "Start with the topic name and then add the summary. Split the topics by two empty lines"
                              "Your response is going to be used to create a pdf, so make sure that you use the right"
                              "format.")]

    for result in results:
        messages.append(result)
        for tool_call in result.tool_calls:
            selected_tool = {"summary-tool": summarize_tool}[tool_call["name"].lower()]
            tool_msg = selected_tool.invoke(tool_call)
            messages.append(tool_msg)

    summary = llm_with_tools.invoke(messages)

    chat_template = ChatPromptTemplate.from_messages(messages)

    parser = StrOutputParser()

    chain = chat_template | llm_with_tools | parser

    result_final = chain.invoke({})

    return result_final
