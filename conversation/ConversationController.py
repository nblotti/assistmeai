import json
from typing import Annotated

from fastapi import APIRouter, Query, Depends
from fastapi import Response

from CustomEncoder import CustomEncoder
from DependencyManager import message_dao_provider, conversation_dao_provider, document_dao_provider
from conversation.Conversation import Conversation
from conversation.ConversationRepository import ConversationRepository
from document.DocumentsRepository import DocumentsRepository
from message.MessageRepository import MessageRepository

router_conversation = APIRouter(
    prefix="/conversation",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)

'''
------------------------------------------------------------------------------------------------------------------------

Conversation entry point

------------------------------------------------------------------------------------------------------------------------
'''

message_repository_dep = Annotated[MessageRepository, Depends(message_dao_provider.get_dependency)]
conversation_repository_dep = Annotated[ConversationRepository, Depends(conversation_dao_provider.get_dependency)]
document_repository_dep= Annotated[DocumentsRepository, Depends(document_dao_provider.get_dependency)]
@router_conversation.get("/perimeter/{perimeter}/")
async def conversations(conversation_repository: conversation_repository_dep, perimeter: str):
    res = conversation_repository.get_conversation_by_perimeter(perimeter)
    return json.loads(json.dumps(res, cls=CustomEncoder))


@router_conversation.get("/document/{document_id}/")
async def conversations(conversation_repository: conversation_repository_dep, document_id: str,
                        user_id: str = Query(None)):
    res = conversation_repository.get_conversation_by_document_id(document_id, user_id)
    return json.loads(json.dumps(res, cls=CustomEncoder))


@router_conversation.delete("/{conversation_id}/")
async def conversations(conversation_repository: conversation_repository_dep, conversation_id: str):
    conversation_repository.delete(conversation_id)

    return Response(status_code=200)


@router_conversation.post("/")
async def conversation(conversation_repository: conversation_repository_dep,
                       document_repository: document_repository_dep, new_conversation: Conversation):
    res = conversation_repository.save(new_conversation)

    if res.pdf_id != 0:
        doc = document_repository.get_by_id(res.pdf_id)
        res.pdf_name = doc[0]

    return res
