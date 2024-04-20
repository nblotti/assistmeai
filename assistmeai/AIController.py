from fastapi import APIRouter
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.chains.llm import LLMChain
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories.file import FileChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from memories.SqlMessageHistory import SqlMessageHistory, build_memory
from pdf.SqliteDAO import SqliteDAO
from vector_stores.pinecone import build_retriever

router_ai = APIRouter(
    prefix="/ai",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)


@tool(return_direct=True)
def list_documents() -> str:
    """List all documents"""
    sqlitedao = SqliteDAO()
    return sqlitedao.list()


tools = [list_documents]
chat = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0, verbose=True)


@router_ai.get("/")
async def ai_command(command: str, conversation_id: str, user_id: str, blob_id: str):
    # Choose the LLM that will drive the agent
    # Only certain models support this

    chain = ConversationalRetrievalChain.from_llm(
        llm=chat,
        memory=build_memory(conversation_id,blob_id),
        retriever=build_retriever(user_id, blob_id),
    )

    json_return = chain.run(command)
    return json_return
