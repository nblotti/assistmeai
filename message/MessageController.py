import json
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi import Response

from ProviderManager import message_dao_provider
from message import MessageRepository

router_message = APIRouter(
    prefix="/message",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)


message_repository_dep = Annotated[MessageRepository, Depends(message_dao_provider)]


'''
------------------------------------------------------------------------------------------------------------------------

Messages entry point

------------------------------------------------------------------------------------------------------------------------
'''


@router_message.get("/")
async def conversation(message_repository: message_repository_dep, conversation_id: str):
    res = message_repository.get_all_messages_by_conversation_id(conversation_id)
    return res


@router_message.delete("/")
async def conversation(message_repository: message_repository_dep,conversation_id: str):
    message_repository.delete_by_conversation_id(conversation_id)
    return Response(status_code=200)


