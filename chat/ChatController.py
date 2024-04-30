import json
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi import Response
from langchain.agents import OpenAIFunctionsAgent, create_openai_tools_agent, AgentExecutor, create_tool_calling_agent
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.chains.qa_with_sources.retrieval import RetrievalQAWithSourcesChain
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.chains.router import MultiRetrievalQAChain
from langchain_community.retrievers.wikipedia import WikipediaRetriever
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain_core.retrievers import BaseRetriever
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from chat.Conversation import Conversation
from config import load_config
from chat.InteractionManager import InteractionManager
from chat.SqliteDAO import SqliteDAO
from embeddings.CustomPineconeRetriever import CustomPineconeRetriever, QueryType
from memories.SqlMessageHistory import build_document_memory
from tools.tools import get_document_retreiver, get_wikipedia_retreiver
from vector_stores.pinecone import build_all_documents_retriever, build_specific_document_retriever

chat_ai = APIRouter(
    prefix="/chat",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)

interaction_manager_provider = load_config()

chat = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0, verbose=True)


@chat_ai.delete("/")
async def delete_all(interaction_manager: InteractionManager = Depends(interaction_manager_provider.get_dependency)):
    interaction_manager.delete_all()

    return Response(status_code=200)


'''
------------------------------------------------------------------------------------------------------------------------

Conversation entry point

------------------------------------------------------------------------------------------------------------------------
'''


@chat_ai.get("/conversations/perimeter/{perimeter}/")
async def conversations(perimeter: str,
                        interaction_manager: InteractionManager = Depends(interaction_manager_provider.get_dependency)):
    res = interaction_manager.get_conversation_by_perimeter(perimeter)
    return json.loads(json.dumps(res, cls=CustomEncoder))


@chat_ai.get("/conversations/document/{document_id}/")
async def conversations(document_id: str, user_id: str = Query(None),
                        interaction_manager: InteractionManager = Depends(interaction_manager_provider.get_dependency)):
    res = interaction_manager.get_conversation_by_document_id(document_id, user_id)
    return json.loads(json.dumps(res, cls=CustomEncoder))



@chat_ai.delete("/conversations/{conversation_id}/")
async def conversations(conversation_id: str,
                        interaction_manager: InteractionManager = Depends(interaction_manager_provider.get_dependency)):
    interaction_manager.delete_by_conversation_id(conversation_id)

    return Response(status_code=200)


@chat_ai.post("/conversations/")
async def conversation(conversation: Conversation,
                       interaction_manager: InteractionManager = Depends(interaction_manager_provider.get_dependency)):
    res = interaction_manager.save(conversation)
    return res


'''
------------------------------------------------------------------------------------------------------------------------

Messages entry point

------------------------------------------------------------------------------------------------------------------------
'''


@chat_ai.get("/messages/")
async def conversation(conversation_id: str,
                       interaction_manager: InteractionManager = Depends(interaction_manager_provider.get_dependency)):
    res = interaction_manager.get_messages(conversation_id)
    return res


'''
------------------------------------------------------------------------------------------------------------------------

Messages entry point

------------------------------------------------------------------------------------------------------------------------
'''


@chat_ai.get("/command/v1/")
async def message(command: str, conversation_id: str, perimeter: str = Query(...),
                  interaction_manager: InteractionManager = Depends(interaction_manager_provider.get_dependency)):
    # Choose the LLM that will drive the agent
    # Only certain models support this
    cur_conversation = interaction_manager.get_conversation_by_id(conversation_id)
    wikipedia_tool = get_wikipedia_retreiver()

    memory = build_document_memory(interaction_manager, conversation_id)

    if cur_conversation.pdf_id is None or cur_conversation.pdf_id == "-1":
        rag_retriever = CustomPineconeRetriever(QueryType.PERIMETER,perimeter)
    else:
        rag_retriever = CustomPineconeRetriever(QueryType.DOCUMENT,cur_conversation.pdf_id)

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


@chat_ai.get("/command/")
async def message(command: str, conversation_id: str, perimeter: list[str] = Query(...),
                  interaction_manager: InteractionManager = Depends(interaction_manager_provider.get_dependency)):
    # Choose the LLM that will drive the agent
    # Only certain models support this
    cur_conversation: Conversation = interaction_manager.get_conversation_by_id(conversation_id)
    doc_tool = get_document_retreiver(cur_conversation, perimeter)
    wikipedia_tool = get_wikipedia_retreiver()

    loc_tools = [doc_tool, wikipedia_tool]

    memory = build_document_memory(interaction_manager, conversation_id)

    prompt = ChatPromptTemplate(
        messages=[
            SystemMessage(content=("Your are an AI that has access to a set of tools.\n"
                                   "Do not try to answer based on your knowledge without data provided by the tools.\n"
                                   "Instead tell the user that you did not found any relevant information.\n"
                                   "Do not make any assumptions about the questions.")),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ]
    )

    agent = create_tool_calling_agent(chat, loc_tools, prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        verbose=True,
        tools=loc_tools,
        memory=memory
    )

    result = agent_executor.invoke({"input": command})

    return result["output"]


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%d.%m.%Y")  # Convert datetime object to string in "dd.MM.YYYY" format
        return json.JSONEncoder.default(self, obj)
