import json
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi import Response
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from chat.Conversation import Conversation
from config import load_config
from chat.InteractionManager import InteractionManager
from chat.SqliteDAO import SqliteDAO
from memories.SqlMessageHistory import build_document_memory
from vector_stores.pinecone import build_all_documents_retriever, build_specific_document_retriever

chat_ai = APIRouter(
    prefix="/chat",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)

interaction_manager_provider = load_config()


@tool(return_direct=True)
def list_documents() -> str:
    """List all documents"""
    sqlitedao = SqliteDAO()
    return sqlitedao.list()


tools = [list_documents]
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


@chat_ai.get("/conversations/{user_id}/")
async def conversations(user_id: str,
                        interaction_manager: InteractionManager = Depends(interaction_manager_provider.get_dependency)):
    res = interaction_manager.get_conversation_by_user_id(user_id)
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

@chat_ai.get("/command/")
async def message(command: str, conversation_id: str,
                  interaction_manager: InteractionManager = Depends(interaction_manager_provider.get_dependency)):
    # Choose the LLM that will drive the agent
    # Only certain models support this

    cur_conversation: Conversation = interaction_manager.get_conversation_by_id(conversation_id)

    if cur_conversation.pdf_id != "-1":
        retriever = build_all_documents_retriever(cur_conversation.user_id)
    else:
        retriever = build_specific_document_retriever(cur_conversation.user_id, cur_conversation.pdf_id)

    chain = ConversationalRetrievalChain.from_llm(
        llm=chat,
        memory=build_document_memory(interaction_manager, conversation_id),
        retriever=retriever
    )

    json_return = chain.run(command)
    return json_return


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%d.%m.%Y")  # Convert datetime object to string in "dd.MM.YYYY" format
        return json.JSONEncoder.default(self, obj)
