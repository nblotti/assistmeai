from typing import Annotated

from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from DependencyManager import assistant_manager_provider, conversation_dao_provider
from assistants.Assistant import Assistant
from assistants.AssistantCommand import AssistantCommand
from assistants.AssistantsManager import AssistantManager
from conversation.Conversation import Conversation
from conversation.ConversationRepository import ConversationRepository

router_assistant = APIRouter(
    prefix="/assistants",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)

assistant_manager_dep = Annotated[AssistantManager, Depends(assistant_manager_provider.get_dependency)]
conversation_repository_dep = Annotated[ConversationRepository, Depends(conversation_dao_provider.get_dependency)]


@router_assistant.post("/command/")
def execute_get_command(assistant_command: AssistantCommand, assistant_manager: assistant_manager_dep
                        ) -> JSONResponse:
    try:
        result = assistant_manager.execute_command(assistant_command.conversation_id, assistant_command.command)
        return JSONResponse(content={"result": result})
    except Exception as e:
        print(f"Error occurred: {e}")
        raise


@router_assistant.get("/command/")
async def execute_post_command(assistant_manager: assistant_manager_dep, command: str, conversation_id: str,
                               perimeter: str = None):
    try:
        result = assistant_manager.execute_command(conversation_id, command)
        return JSONResponse(content={"result": result})
    except Exception as e:
        print(f"Error occurred: {e}")
        raise


@router_assistant.post("/")
async def create(assistant: Assistant, assistant_manager: assistant_manager_dep,
                 conversation_repository: conversation_repository_dep):
    conversation: Conversation = Conversation(
        perimeter=assistant.userid,
        description="Assistant - {}".format(assistant.name),
        pdf_id=0
    )

    new_conversation = conversation_repository.save(conversation)
    assistant.conversation_id = new_conversation.id
    # 1 on crée l'assistant
    new_assistant = assistant_manager.save(assistant)

    return new_assistant


@router_assistant.put("/")
async def update(assistant: Assistant, assistant_manager: assistant_manager_dep):
    # 1 on crée l'assistant
    new_assistant = assistant_manager.update(assistant)

    return new_assistant


@router_assistant.get("/{user_id}/")
async def list(assistant_manager: assistant_manager_dep, user_id: str):
    return assistant_manager.get_all_assistant_by_user_id(user_id)


@router_assistant.delete("/{assistant_id}/")
async def delete(assistant_manager: assistant_manager_dep, assistant_id: str):
    # 1 on supprime l'assistant
    assistant_manager.delete_by_assistant_id(assistant_id)
