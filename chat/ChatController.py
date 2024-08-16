import os
import uuid
from typing import Annotated

from fastapi import APIRouter, Query, Depends, HTTPException
from langchain.chains.combine_documents.map_reduce import MapReduceDocumentsChain
from langchain.chains.combine_documents.reduce import ReduceDocumentsChain
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain_core.prompts import PromptTemplate
from starlette.responses import JSONResponse

from DependencyManager import message_dao_provider, conversation_dao_provider
from chat.azure_openai import chat_gpt_35
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
            #verbose=True,
            retriever=rag_retriever,
            return_source_documents=True,
            output_key="result",
            memory=memory
        )

    # Invoke the chain with the command/query
    try:
        result = chain.invoke({"query": command})
        #print(result)  # Or whatever logging mechanism you prefer
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
async def summarize(documents_repository: document_repository_dep,
                    embedding_repository: embeddings_repository_dep,
                    blob_id: str):
    content = documents_repository.get_by_id(blob_id)
    path = "./" + str(uuid.uuid4())

    temp_pdf_file = path + ".pdf"

    with open(temp_pdf_file, "wb") as file_w:
        file_w.write(content[1])

    docs = embedding_repository.create_embeddings(temp_pdf_file)

    # This controls how each document will be formatted. Specifically,
    # it will be passed to `format_document` - see that function for more
    # details.
    document_prompt = PromptTemplate(
        input_variables=["page_content"],
        template="{page_content}"
    )
    document_variable_name = "context"
    llm = chat_gpt_35
    # The prompt here should take as an input variable the
    # `document_variable_name`
    prompt = PromptTemplate.from_template(
        "Summarize this content: {context}"
    )
    llm_chain = LLMChain(llm=llm, prompt=prompt)
    # We now define how to combine these summaries
    reduce_prompt = PromptTemplate.from_template(
        "Combine these summaries: {context}"
    )
    reduce_llm_chain = LLMChain(llm=llm, prompt=reduce_prompt)
    combine_documents_chain = StuffDocumentsChain(
        llm_chain=reduce_llm_chain,
        document_prompt=document_prompt,
        document_variable_name=document_variable_name
    )
    reduce_documents_chain = ReduceDocumentsChain(
        combine_documents_chain=combine_documents_chain,
    )
    chain = MapReduceDocumentsChain(
        llm_chain=llm_chain,
        reduce_documents_chain=reduce_documents_chain,
    )
    # If we wanted to, we could also pass in collapse_documents_chain
    # which is specifically aimed at collapsing documents BEFORE
    # the final call.
    prompt = PromptTemplate.from_template(
        "Collapse this content: {context}"
    )
    llm_chain = LLMChain(llm=llm, prompt=prompt)
    collapse_documents_chain = StuffDocumentsChain(
        llm_chain=llm_chain,
        document_prompt=document_prompt,
        document_variable_name=document_variable_name
    )
    reduce_documents_chain = ReduceDocumentsChain(
        combine_documents_chain=combine_documents_chain,
        collapse_documents_chain=collapse_documents_chain,
    )
    chain = MapReduceDocumentsChain(
        llm_chain=llm_chain,
        reduce_documents_chain=reduce_documents_chain,
    )

    result = chain.invoke(docs)
    # GPT3.5-16k

    try:
        os.remove(temp_pdf_file)
        print(f"File '{temp_pdf_file}' deleted successfully.")
    except OSError as e:
        print(f"Error deleting file '{temp_pdf_file}': {e}")
    return JSONResponse(content={"result": result["output_text"]})

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
        llm=chat_gpt_35,
        #verbose=True,
        retriever=rag_retriever,
        return_source_documents=True,
    )

    result = chain.invoke({"query": command})
    sources = []
    for document in result["source_documents"]:
        sources.append(document.metadata)

    return {"result": result["result"], "sources": sources}
