from typing import Annotated

from fastapi import APIRouter, Depends
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableWithMessageHistory
from starlette.responses import JSONResponse

from DependencyManager import conversation_dao_provider, assistants_dao_provider, message_dao_provider
from assistants import AssistantsRepository
from assistants.Assistant import Assistant
from chat.azure_openai import chat_gpt_35, chat_gpt_4o
from chat.tools import summarize, web_search, get_date
from conversation import ConversationRepository
from conversation.Conversation import Conversation
from memories.SqlMessageHistory import build_agent_memory
from message import MessageRepository

router_assistant = APIRouter(
    prefix="/assistants",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)

conversation_repository_dep = Annotated[ConversationRepository, Depends(conversation_dao_provider.get_dependency)]
assistants_repository_dep = Annotated[AssistantsRepository, Depends(assistants_dao_provider.get_dependency)]
message_repository_dep = Annotated[MessageRepository, Depends(message_dao_provider.get_dependency)]


@router_assistant.get("/command/")
async def message(message_repository: message_repository_dep, conversation_repository: conversation_repository_dep,
                  assistants_repository: assistants_repository_dep,
                  command: str, conversation_id: str, perimeter: str = None):
    # Get the current conversation and build document memory
    assistant: Assistant = assistants_repository.get_assistant_by_conversation_id(conversation_id)

    if assistant.gpt_model_number == "4o":
        local_chat = chat_gpt_4o
    else:
        local_chat = chat_gpt_35

    memory = build_agent_memory(message_repository, assistant.conversation_id)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "{}.\nYou have access to tools. Use them if if need to.Somme tools will require an assistant id which is {}."
                "If you don't know, do not invent, just say it.".format(assistant.description, assistant.id)

            ),
            ("placeholder", "{messages}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )

    if assistant.use_documents:

        tools = [get_date, web_search, summarize]

        agent = create_openai_tools_agent(llm=local_chat, tools=tools, prompt=prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

        conversational_agent_executor = RunnableWithMessageHistory(
            agent_executor,
            lambda session_id: memory,
            input_messages_key="messages",
            output_messages_key="output",
        )

        try:
            result = conversational_agent_executor.invoke(
                {"messages": [HumanMessage(command)]},
                {"configurable": {"session_id": "unused"}},
            )
            return JSONResponse(content={"result": result["output"]})
        except Exception as e:
            print(f"Error occurred: {e}")
            raise

    else:
        tools = [get_date, web_search]
        agent = create_openai_tools_agent(llm=local_chat, tools=tools, prompt=prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

        conversational_agent_executor = RunnableWithMessageHistory(
            agent_executor,
            lambda session_id: memory,
            input_messages_key="messages",
            output_messages_key="output",
        )

        try:
            result = conversational_agent_executor.invoke(
                {"messages": [HumanMessage(f"'''{command}'''")]},
                {"configurable": {"session_id": "unused"}},
            )
            return JSONResponse(content={"result": result["output"]})
        except Exception as e:
            print(f"Error occurred: {e}")
            raise


@router_assistant.post("/")
async def create(assistant: Assistant, assistants_repository: assistants_repository_dep,
                 conversation_repository: conversation_repository_dep):
    conversation: Conversation = Conversation(
        perimeter=assistant.userid,
        description="Assistant - {}".format(assistant.name),
        pdf_id=0
    )

    new_conversation = conversation_repository.save(conversation)
    assistant.conversation_id = new_conversation.id
    # 1 on crée l'assistant
    new_assistant = assistants_repository.save(assistant)

    return new_assistant


@router_assistant.put("/")
async def update(assistant: Assistant, assistants_repository: assistants_repository_dep):
    # 1 on crée l'assistant
    new_assistant = assistants_repository.update(assistant)

    return new_assistant


@router_assistant.get("/{user_id}/")
async def list(assistants_repository: assistants_repository_dep, user_id: str):
    return assistants_repository.get_all_assistant_by_user_id(user_id)


@router_assistant.delete("/{assistant_id}/")
async def delete(assistants_repository: assistants_repository_dep, assistant_id: str):
    # 1 on supprime l'assistant
    assistants_repository.delete_by_assistant_id(assistant_id)
