from typing import Annotated

from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from ProviderManager import assistant_manager_provider, conversation_dao_provider
from assistants.Assistant import Assistant, AssistantCreate
from assistants.AssistantCommand import AssistantCommand
from assistants.AssistantsManager import AssistantManager
from assistants.VBAAssistantCommand import VBAAssistantCommand
from assistants.VBAPPTPresentationAssistantCommand import VBAPPTPresentationAssistantCommand
from conversation.Conversation import Conversation, ConversationCreate
from conversation.ConversationRepository import ConversationRepository

router_assistant = APIRouter(
    prefix="/assistants",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)

assistant_manager_dep = Annotated[AssistantManager, Depends(assistant_manager_provider)]
conversation_repository_dep = Annotated[ConversationRepository, Depends(conversation_dao_provider)]


@router_assistant.post("/command/")
def execute_post_command(assistant_command: AssistantCommand, assistant_manager: assistant_manager_dep) -> JSONResponse:
    try:
        result = assistant_manager.execute_command(assistant_command.conversation_id,
                                                   assistant_command.command)
        return JSONResponse(content={"result": result})
    except Exception as e:
        print(f"Error occurred: {e}")
        raise


@router_assistant.post("/command/vba/")
def execute_get_command(assistant_command: VBAAssistantCommand,
                        assistant_manager: assistant_manager_dep) -> JSONResponse:
    try:
        result = assistant_manager.execute_command_vba(assistant_command.conversation_id,
                                                       assistant_command.command,
                                                       assistant_command.use_documentation, assistant_command.memory)
        return result
    except Exception as e:
        print(f"Error occurred: {e}")
        raise


@router_assistant.post("/command/vba/powerpoint/")
def execute_get_command(assistant_command: VBAPPTPresentationAssistantCommand,
                        assistant_manager: assistant_manager_dep) -> JSONResponse:
    try:
        result = assistant_manager.execute_powerpoint_command_vba(assistant_command.conversation_id,
                                                                  assistant_command.command,
                                                                  assistant_command.use_documentation)
        return result
    except Exception as e:
        print(f"Error occurred: {e}")
        raise


@router_assistant.get("/command/")
async def execute_get_command(assistant_manager: assistant_manager_dep, command: str, conversation_id: str,
                              perimeter: str = None):
    try:
        result = assistant_manager.execute_command(conversation_id, command)
        return JSONResponse(content={"result": result})
    except Exception as e:
        print(f"Error occurred: {e}")
        raise


@router_assistant.post("/")
async def create(assistant: AssistantCreate, assistant_manager: assistant_manager_dep,
                 conversation_repository: conversation_repository_dep):
    conversation: ConversationCreate = ConversationCreate(
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
async def update(assistant: AssistantCreate, assistant_manager: assistant_manager_dep):
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
