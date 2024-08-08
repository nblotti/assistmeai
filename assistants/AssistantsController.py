from typing import Annotated

from fastapi import APIRouter, Depends
from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate
from starlette.responses import JSONResponse

from DependencyManager import conversation_dao_provider, assistants_dao_provider, message_dao_provider
from assistants import AssistantsRepository
from assistants.Assistant import Assistant
from chat.azure_openai import chat_gpt_35, chat_gpt_4o
from conversation import ConversationRepository
from conversation.Conversation import Conversation
from memories.SqlMessageHistory import build_memory
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
                  assistants_repository: assistants_repository_dep, command: str,
                  conversation_id: str):
    # Get the current conversation and build document memory
    assistant: Assistant = assistants_repository.get_assistant_by_conversation_id(conversation_id)

    if assistant.gpt_model_number == "4o":
        local_chat = chat_gpt_4o
    else:
        local_chat = chat_gpt_35

    memory = build_memory(message_repository, assistant.conversation_id)
    # Load a simpler LLMChain without retriever
    template = """
    {system}
    {chat_history}
    Human: {query}
    Chatbot:"""
    prompt = PromptTemplate(
        input_variables=["system", "chat_history", "query"],
        template=template
    )
    chain = LLMChain(
        prompt=prompt,
        llm=local_chat,
        verbose=True,
        memory=memory,
        output_key="result"
    )

    # Invoke the chain with the command/query
    try:
        result = chain.invoke({"system": assistant.description, "query": command})
        return JSONResponse(content={"result": result["result"]})
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
